import os
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import tkinter.scrolledtext
from bldg_regularization import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Building Boundary Regularization V1.0')
        self.in_fp, self.out_fp = None, None
        self.poly_source, self.poly_out, self.poly_in, self.poly_ids = None, None, None, None
        self.IOU_final, self.group_ids, self.direction, self.factor = None, None, None, None

        # App Frames
        self.setting_frame = tk.LabelFrame(self, text="Setting View")
        self.table_frame = tk.LabelFrame(self, text="Table View")
        self.display_frame = tk.LabelFrame(self, text="Visualization View")

        self.setting_frame.grid(row=0, column=0, padx=5, pady=5, sticky='n')
        self.table_frame.grid(row=0, column=1, padx=5, pady=5, sticky='n')
        self.display_frame.grid(row=0, column=2, padx=5, pady=5, sticky='n')

        # Button Frame
        self.open_file_btn = tk.Button(self.setting_frame, text='Open File', command=self.open_file)
        self.open_file_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.save_file_btn = tk.Button(self.setting_frame, text='Save File', command=self.save_file)
        self.save_file_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.open_file_text = tk.Entry(self.setting_frame)
        self.open_file_text.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.save_file_text = tk.Entry(self.setting_frame)
        self.save_file_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.simple_label = tk.Label(self.setting_frame, text="Simplification threshold (no while <=0)")
        self.simple_label.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.simple_text = tk.Entry(self.setting_frame)
        self.simple_text.insert(0, '0.5')
        self.simple_text.bind("<FocusOut>", self.validate_entry)
        self.simple_text.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        self.LOD_label = tk.Label(self.setting_frame, text="Level of details")
        self.LOD_label.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        self.LOD_combox = ttk.Combobox(self.setting_frame, values=['1', '2', '3'], state='readonly')
        self.LOD_combox.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.LOD_combox.current(0)

        self.RC_label = tk.Label(self.setting_frame, text="Regularization criterion")
        self.RC_label.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        self.RC_combox = ttk.Combobox(self.setting_frame, values=['Min bounding', 'Max IOU'], state='readonly')
        self.RC_combox.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.RC_combox.current(0)

        self.TP_label = tk.Label(self.setting_frame, text="Touched polygons")
        self.TP_label.grid(row=5, column=0, sticky="ew", padx=5, pady=5)

        self.TP_combox = ttk.Combobox(self.setting_frame, values=['Group', 'Separate'], state='readonly')
        self.TP_combox.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        self.TP_combox.current(0)

        self.run_btn = tk.Button(self.setting_frame, text='Run', command=self.process)
        self.run_btn.grid(row=6, column=0, sticky="ew", padx=5, pady=5)

        self.view_btn = tk.Button(self.setting_frame, text='View', state='disabled', command=self.draw_all)
        self.view_btn.grid(row=6, column=1, sticky="ew", padx=5, pady=5)

        self.process_bar = ttk.Progressbar(self.setting_frame, mode='determinate')
        self.process_bar.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.text_area = tk.scrolledtext.ScrolledText(self.setting_frame, wrap=tk.WORD, width=40, height=10,
                                                      state='disabled')
        self.text_area.grid(row=8, column=0, columnspan=2, sticky="ewn", padx=5, pady=5)
        self.write_log('**********Polygon Regularization**********\n')
        self.write_log(f'Date: {time.ctime()}\n')
        self.write_log('Please select the shapefile...\n')

        # Table Frame
        self.table_view = ttk.Treeview(self.table_frame, columns=('gid', 'iou', 'dir', 'a'), height=20, selectmode="browse")
        self.table_view.grid(row=0, column=0, sticky="ewn", padx=5, pady=5)
        self.table_view.heading('#0', text='Poly_ID')
        self.table_view.column("# 0", anchor='center', stretch=False, width=80)
        self.table_view.heading('gid', text='Group_ID')
        self.table_view.column('gid', anchor='center', stretch=False, width=80)
        self.table_view.heading('iou', text='IOU')
        self.table_view.column('iou', anchor='center', stretch=False, width=80)
        self.table_view.heading('dir', text='Direction')
        self.table_view.column('dir', anchor='center', stretch=False, width=80)
        self.table_view.heading('a', text='Factor')
        self.table_view.column('a', anchor='center', stretch=False, width=80)
        self.table_view.bind("<Double-1>", self.draw_one)

        self.table_scroll = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.table_view.yview)
        self.table_scroll.grid(row=0, column=1, sticky="ns")
        self.table_view.configure(yscrollcommand=self.table_scroll.set)

        # Display frame
        self.source_flag = tk.BooleanVar()
        self.source_check = tk.Checkbutton(self.display_frame, text='Source', variable=self.source_flag, fg='red')
        self.source_check.grid(row=0, column=0, sticky="n", padx=25, pady=5)

        self.simple_flag = tk.BooleanVar()
        self.simple_check = tk.Checkbutton(self.display_frame, text='Simplified', variable=self.simple_flag, fg='blue')
        self.simple_check.select()
        self.simple_check.grid(row=0, column=1, sticky="n", padx=25, pady=5)

        self.out_flag = tk.BooleanVar()
        self.out_check = tk.Checkbutton(self.display_frame, text='Regularized', variable=self.out_flag, fg='green')
        self.out_check.select()
        self.out_check.grid(row=0, column=2, sticky="n", padx=25, pady=5)

        fig = plt.Figure(figsize=(4, 4), dpi=97)
        self.ax = fig.add_subplot()
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.axis('off')
        fig.subplots_adjust(left=0.02, bottom=0.02, right=0.98, top=0.98)

        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.display_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        App.resizable(self, width=0, height=0)

    def open_file(self):
        self.in_fp = tk.filedialog.askopenfilename(title="Select file for processing",
                                                   filetypes=(("Shapefiles", "*.shp"), ("all files", "*.*")))

        self.open_file_text.delete(0, "end")
        self.open_file_text.insert(0, self.in_fp)

        if self.in_fp != '':
            temp = self.in_fp.split('.')
            self.out_fp = temp[0] + '_out.' + temp[1]

            self.save_file_text.delete(0, "end")
            self.save_file_text.insert(0, self.out_fp)

    def save_file(self):
        self.out_fp = tk.filedialog.askopenfilename()

        if self.out_fp != '':
            self.save_file_text.delete(0, "end")
            self.save_file_text.insert(0, self.out_fp)

    def validate_entry(self, event):
        self.simple_check.configure(state='normal')
        try:
            v = float(self.simple_text.get())

            if v <= 0:
                self.simple_text.delete(0, 'end')
                self.simple_text.insert(0, 'No Simplification')
                self.simple_check.deselect()
                self.simple_check.configure(state='disabled')
        except:
            self.simple_text.delete(0, 'end')
            self.simple_text.insert(0, '0.5')

    def draw_one(self, event):
        self.ax.clear()
        self.ax.axis('off')
        idx = self.table_view.index(self.table_view.selection()[0])
        poly_source = self.poly_source[idx]
        poly_in = self.poly_in[idx]
        poly_out = self.poly_out[idx]
        self.ax.set_title(f'Visualization of Poly_{idx}', y=0.95)

        if self.source_flag.get():
            self.ax.plot(*poly_source.exterior.xy, 'r-')
        if self.simple_flag.get():
            self.ax.plot(*poly_in.exterior.xy, 'b-')
        if self.out_flag.get():
            self.ax.plot(*poly_out.exterior.xy, 'g-')

        self.plot_canvas.draw()
        self.update()

    def draw_all(self):
        self.ax.clear()
        self.ax.axis('off')
        self.ax.set_title(f'Visualization of All Polygons', y=0.95)

        for i in range(len(self.poly_in)):
            if self.source_flag.get():
                self.ax.plot(*self.poly_source[i].exterior.xy, 'r-')
            if self.simple_flag.get():
                self.ax.plot(*self.poly_in[i].exterior.xy, 'b-')
            if self.out_flag.get():
                self.ax.plot(*self.poly_out[i].exterior.xy, 'g-')

        self.plot_canvas.draw()
        self.update()

    def write_log(self, s):
        self.text_area.configure(state='normal')
        self.text_area.insert('end', s)
        self.text_area.configure(state='disabled')
        self.text_area.see('end')

    def process(self):
        self.ax.clear()
        self.ax.axis('off')
        self.plot_canvas.draw()
        self.update()

        fp = self.open_file_text.get()
        simple_th = float(self.simple_text.get())
        lod = int(self.LOD_combox.get())
        criterion = self.RC_combox.get()
        group = self.TP_combox.get()
        group_flag = True if group == 'Group' else False
        alphas = [0] if criterion == 'Min bounding' else [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]

        for row in self.table_view.get_children():
            self.table_view.delete(row)

        if os.path.exists(fp):
            time_start = time.time()
            poly_out, poly_in, IOU_final, poly_ids, group_ids, direction, factor = [], [], [], [], [], [], []
            poly_id, group_id = 0, 0
            self.write_log(' ' * 40 + '\n')
            self.write_log(f'File path:  {fp}\n')
            self.write_log(f'Threshold:  {simple_th}\n')
            self.write_log(f'      LOD:  {lod}\n')
            self.write_log(f'Criterion:  {criterion}\n')
            self.write_log(f'  Touched:  {group}\n')
            self.write_log(' ' * 40 + '\n')
            self.write_log(f'Loading shapefile...\n')

            poly_list, poly_source, poly_num, gdf = load_shp(fp, group_flag, simple_th)
            self.write_log(f'   Polygon num:  {poly_num}\n')
            self.update()

            if group_flag:
                self.write_log(f'     Group num:  {len(poly_list)}\n')

            self.write_log(' ' * 40 + '\n')
            self.write_log(f'Start regularizing polygons...\n')
            self.write_log(' ' * 40 + '\n')

            for poly in poly_list:
                IOUs, poly_regs, alpha_temp, degs = [], [], [], [item for item in range(180)]
                centroid = [shapely.centroid(item) for item in poly]

                for deg in degs:
                    poly_rotate = rotate_geom(poly, centroid, deg)
                    poly_reg, IOU, alpha = regularize_geom(poly_rotate, lod=lod, alphas=alphas)
                    poly_reg = rotate_geom(poly_reg, centroid, - deg)

                    IOUs.append(np.mean(IOU))
                    poly_regs.append(poly_reg)
                    alpha_temp.append(alpha)

                bid = np.argmax(IOUs)
                poly_clean = process_overlap(poly_regs[bid])

                for i in range(len(poly)):
                    poly_in.append(poly[i])
                    poly_out.append(poly_clean[i])
                    IOU = poly[i].intersection(poly_clean[i]).area / poly[i].union(poly_clean[i]).area
                    IOU_final.append(IOU)
                    poly_ids.append(poly_id)
                    group_ids.append(group_id)
                    direction.append(degs[bid])
                    factor_best = alpha_temp[bid][i]
                    factor.append(factor_best)

                    self.process_bar['value'] = int(100 * poly_id / poly_num)
                    self.table_view.insert('', 'end', text=f'{poly_id}',
                                           values=[f'{group_id}', f'{IOU:.4f}',
                                                   f'{degs[bid]}°', f'{1 - factor_best:.2f}'])
                    poly_id += 1
                    self.update()
                group_id += 1

            df = pd.DataFrame({
                'Poly_ID': poly_ids,
                'Group_ID': group_ids,
                'IOU': IOU_final,
                'Direction': direction,
                'Factor': factor
            })

            time_end = time.time()
            self.write_log(f'Processing Time: {time_end - time_start:.4f}s\n')

            if not gdf.crs:
                out_gdf = gpd.GeoDataFrame(df, geometry=poly_out, crs='')
                self.write_log('No CRS found.\n')
            else:
                out_gdf = gpd.GeoDataFrame(df, geometry=poly_out, crs=gdf.crs.to_epsg())
                self.write_log(f'CRS: {gdf.crs.to_epsg()}.\n')

            self.poly_source = poly_source
            self.poly_out = poly_out
            self.poly_in = poly_in
            self.IOU_final = IOU_final
            self.poly_ids = poly_ids
            self.group_ids = group_ids
            self.direction = direction
            self.factor = factor
            self.process_bar['value'] = 0

            self.write_log(' ' * 40 + '\n')
            self.write_log('Statistic:\n')
            self.write_log(f'   IOU Max:    {np.max(IOU_final):.4f}\n')
            self.write_log(f'   IOU Min:    {np.min(IOU_final):.4f}\n')
            self.write_log(f'   IOU AVG:    {np.mean(IOU_final):.4f}\n')
            self.write_log(f'   IOU STD:    {np.std(IOU_final):.4f}\n')
            self.write_log(' ' * 40 + '\n')
            self.write_log(f'Done!\nPress View button to display the results, or doubleclick table to display one.\n')
            self.write_log(' ' * 40 + '\n')
            out_gdf.to_file(self.out_fp)
            self.write_log(f'Results have been saved in: {self.out_fp}\n')
            self.view_btn.configure(state='normal')
        else:
            self.write_log(' ' * 40 + '\n')
            self.write_log('File not exist, please retry...')

        self.write_log(' ' * 40 + '\n')
        self.write_log('**********Polygon Regularization**********\n')
        self.write_log(f'Date: {time.ctime()}\n')
        self.write_log('Please select the shapefile...\n')
        self.update()


if __name__ == "__main__":
    win = App()
    win.mainloop()
