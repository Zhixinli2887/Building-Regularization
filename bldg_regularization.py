import shapely
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.validation import make_valid


def rotate_geom(geoms, centroids, deg):
    results = []

    for i in range(len(geoms)):
        results.append(shapely.affinity.rotate(geoms[i], deg, origin=centroids[i]))

    return results


def intersect_line(sp, vec):
    sa, sb = sp[:- 1], sp[:- 1] + vec[:- 1]
    sc, sd = sp[1:], sp[1:] + vec[1:]

    a1 = sb[:, 1] - sa[:, 1]
    b1 = sa[:, 0] - sb[:, 0]
    c1 = a1 * sa[:, 0] + b1 * sa[:, 1]

    a2 = sd[:, 1] - sc[:, 1]
    b2 = sc[:, 0] - sd[:, 0]
    c2 = a2 * sc[:, 0] + b2 * sc[:, 1]
    det = a1 * b2 - a2 * b1
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.array([(b2 * c1 - b1 * c2) / det, (a1 * c2 - a2 * c1) / det]).T


def regularize_geom(geoms, lod=1, alphas=None):
    geom_out, iou_out, alpha_out = [], [], []
    vecs = [[np.cos(0), np.sin(0)], [np.cos(np.pi / 2), np.sin(np.pi / 2)]]

    for i in range(1, lod):
        sep = 90 / (i + 1)

        for j in range(i):
            vecs.append([np.cos(np.deg2rad(sep * (j + 1))), np.sin(np.deg2rad(sep * (j + 1)))])
            vecs.append([np.cos(np.deg2rad(sep * (j + 1) + 90)), np.sin(np.deg2rad(sep * (j + 1) + 90))])

    vecs = np.array(vecs)

    for geom in geoms:
        geom_temp, iou_temp = [], []

        for alpha in alphas:
            geom_np_new = []
            geom_np = np.array(geom.exterior.coords[:])
            lines = np.array([[geom_np[i], geom_np[i + 1]] for i in range(len(geom_np) - 1)])
            edge_sp, edge_vec, line_cls = project_line(lines, vecs, alpha)
            edge_sp = np.append(edge_sp, [edge_sp[0]], axis=0)
            edge_vec = np.append(edge_vec, [edge_vec[0]], axis=0)
            line_cls = np.append(line_cls, [line_cls[0]], axis=0)
            lines = np.append(lines, [lines[0]], axis=0)

            pns = intersect_line(edge_sp, edge_vec)
            pas = project_point(edge_sp[:- 1], edge_vec[:- 1], lines[:-1, 1, :])
            pbs = project_point(edge_sp[1:], edge_vec[1:], lines[:-1, 1, :])

            for i in range(len(edge_sp) - 1):

                if line_cls[i] != line_cls[i + 1]:
                    geom_np_new.append(pns[i])
                else:
                    geom_np_new.append(pas[i])
                    geom_np_new.append(pbs[i])

            geom_np_new.append(geom_np_new[0])
            geom_np_new = np.array(geom_np_new)
            geom_new = fix_invalid(Polygon(geom_np_new))
            iou = geom_new.intersection(geom).area / geom_new.union(geom).area
            geom_temp.append(geom_new)
            iou_temp.append(iou)

        idx = np.argmax(iou_temp)
        alpha_out.append(alphas[idx])
        iou_out.append(iou_temp[idx])
        geom_out.append(geom_temp[idx])

    return geom_out, iou_out, alpha_out


def fix_invalid(geom):

    if not geom.is_valid:
        geom_valid = make_valid(geom)
        items, areas = [], []

        if geom_valid.geom_type in ['MultiPolygon', 'GeometryCollection']:
            for item in geom_valid.geoms:
                if item.geom_type == 'Polygon':
                    items.append(item)
                    areas.append(item.area)
                elif item.geom_type == 'MultiPolygon':
                    for item_sub in item.geoms:
                        items.append(item_sub)
                        areas.append(item_sub.area)

            geom_valid = items[np.argmax(areas)]
        return geom_valid
    else:
        return geom


def project_point(ls, ln, p):
    return ls + np.multiply(ln, np.einsum('ij,ij->i', p - ls, ln)[:, np.newaxis])


def project_line(lines, vecs, lr=0.5):
    line_vec = lines[:, 1, :] - lines[:, 0, :]
    line_cls = classify_line(line_vec, vecs)
    pps = project_point(lines[:, 0], vecs[line_cls], lines[:, 1])
    dets = ((lines[:, 1, 0] - lines[:, 0, 0]) * (pps[:, 1] - lines[:, 0, 1]) -
            (lines[:, 1, 1] - lines[:, 0, 1]) * (pps[:, 0] - lines[:, 0, 0]))
    spr = lines[:, 0] + lr * (lines[:, 1] - lines[:, 0])
    spl = lines[:, 1] + lr * (lines[:, 0] - lines[:, 1])
    sps = np.where(dets.reshape(-1, 1) > 0, spr, spl)
    return sps, vecs[line_cls], line_cls


def classify_line(line_vec, edge_vec):
    dets = line_vec @ edge_vec.T
    angles = np.arccos(np.clip(dets / np.linalg.norm(line_vec, axis=1).reshape(-1, 1), - 1.0, 1.0))
    degrees = np.rad2deg(np.where(dets < 0, np.pi - angles, angles))
    return np.argmin(degrees, axis=1)


def process_overlap(geoms):
    if len(geoms) > 1:
        areas = [geom.area for geom in geoms]
        ids = np.argsort(areas)

        for i in ids:
            for j in [item for item in ids if item != i]:
                if geoms[i].intersects(geoms[j]):
                    geoms[i] = geoms[i].difference(geoms[j])

    return geoms


def load_shp(in_fp, group=True, simplify=0.5):
    gdf = gpd.read_file(in_fp)
    geom_list, results, sources = [], [], []

    for index, row in gdf.iterrows():
        geom = row['geometry']
        geom_list.append(geom)

    if group:
        union_geom = gdf.unary_union
        unions = [geom for geom in union_geom.geoms]

        for union in unions:
            ids = np.where(union.intersects(geom_list) == True)[0]

            for item in ids:
                sources.append(geom_list[item])

            if simplify > 0:
                results.append([geom_list[item].simplify(simplify) for item in ids])
            else:
                results.append([geom_list[item] for item in ids])
    else:

        for geom in geom_list:
            sources.append(geom_list[geom])

            if simplify > 0:
                results.append([geom.simplify(simplify)])
            else:
                results.append([geom])

    return results, sources, len(geom_list), gdf


if __name__ == "__main__":
    print('Test case')
    # in_fp = 'Data\\initial_vectorization.shp'

    # plt.plot(geom_np[:, 0], geom_np[:, 1])
    # plt.plot(geom_np_new[:, 0], geom_np_new[:, 1], marker='*')
    # plt.plot(*item.exterior.xy)
    # plt.show()

    # geom_list, geom_num = load_shp(fp)
    # results, IOU_final = [], []

    # for geom in geom_list:
    #     IOUs, geom_regs, degs = [], [], [item for item in range(180)]
    #
    #     for deg in degs:
    #         centroid, geom_rotate = rotate_geom(geom, deg)
    #         geom_reg, IOU = regularize_geom(geom_rotate, lod=1)
    #         geom_reg = rotate_geom_back(geom_reg, centroid, - deg)
    #
    #         IOUs.append(np.mean(IOU))
    #         geom_regs.append(geom_reg)
    #
    #     bid = np.argmax(IOUs)
    #     temp = process_overlap(geom_regs[bid])
    #     c = 1
    #
    #     for item in temp:
    #         plt.plot(*item.exterior.xy)
    #
    #     results.append(process_overlap(geom_regs[bid]))
    #     IOU_final.append(IOUs[bid])
    #
    #     c = 1
