import io

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.pyplot import imread
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

def readTxtTable(file : io.TextIOWrapper):
    rows = []
    cells = []
    for line in file.readlines():
        if line[0] == '#' or line.lstrip(' ') == '\n': continue
        cell = ''
        for i in range(len(line)):
            if line[i] in ' \t':
                if cell != '':
                    cells.append(float(cell))
                cell = ''
            elif line[i] in '-.1234567890':
                cell += line[i]
            elif line[i].isalpha():
                cells.append(line[i::].strip(' ').rstrip('\n'))
                break
            else:
                continue
        rows.append(cells)
        cells = []
    return rows

class PlotManager:
    def __init__(self, figure : Figure):
        """Handles matplotlib plotting operations"""
        self.figure = figure
        self.axes = self.figure.add_subplot(111)
        self.lines = {}  # Dictionary to store line objects {line_id: {data : tuple[float], settings : dict[...]}}
        self.background_image = 'maps\\ortophotoplan_earth_80.jpg'
        self.current_id = 0
        self.default_settings = {
            'line_width': 2,
            'line_color': 'blue',
            'line_style': ':',
            'marker_size': 0,
            'marker_color': 'red',
            'label': f'График:{self.current_id}'}

        self.axes.set_xlabel("Широта")
        self.axes.set_ylabel("Долгота")
        self.axes.grid(True)

    def add_line(self, x_data, y_data, settings=None):
        """Add a new line to the plot"""
        if settings is None:
            settings = self.default_settings.copy()
            
        self.current_id += 1
        line_id = self.current_id
        if not line_id in self.lines:
            self.lines[line_id] = {'data': (x_data, y_data),'settings': settings}

        return line_id
        
    def remove_line(self, line_id):
        """Remove a line from the plot"""
        if line_id in self.lines:
            self.lines.pop(line_id)
            return True
        return False
        
    def update_line_settings(self, line_id, settings):
        """Update settings for a specific line"""
        if line_id in self.lines:
            self.lines[line_id]['settings'].update(settings)
            return True
        return False
        
    def redraw_plot(self):
        """Redraw the entire plot with all lines"""
        self.axes.clear()

        for line_id, line_data in self.lines.items():
            x, y = line_data['data']
            settings = line_data['settings']
            
            self.axes.plot(
                x, y,
                linewidth=settings['line_width'],
                color=settings['line_color'],
                linestyle=settings['line_style'],
                marker='o' if settings['marker_size'] > 0 else None,
                markersize=settings['marker_size'],
                markerfacecolor=settings['marker_color'],
                label=f"График:{line_id}")
            
        self.axes.set_xlabel("Широта")
        self.axes.set_ylabel("Долгота")
        self.axes.set_xlim(-180, 180)
        self.axes.set_ylim(-80, 80)
        self.axes.legend()
    
    def redraw_map(self, path = None):
        if path != None: 
            self.background_image = path
        try:
            image = imread(self.background_image)
            self.axes.imshow(image, zorder=0, extent=[-180.0, 180.0, -80.0, 80.0], interpolation='nearest')
        except Exception as e:
            messagebox.showerror('Ошибка', e)
##-------------------------------------------
#--------------------------------------------
##-------------------------------------------

class PlotApp:
    def __init__(self, root : tk.Tk):
        """Tkinter application with embedded matplotlib plot"""
        self.root = root
        self.root.title("OnMapPlot")
        
        # Create matplotlib components
        self.figure = Figure(figsize=(6, 6), dpi=100)
        self.figure.subplots_adjust(left=0.125, bottom=0.14, right=0.97, top=0.96)
        self.plot_manager = PlotManager(self.figure)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        
        # Track line IDs
        self.active_line_ids = []
        self.current_line_id = None
        
        # Setup UI
        self.setup_ui()
        
        # Plot initial data
        self.update_plot()
        try:
            self.plot_manager.redraw_map()
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось загрузить карту: {str(e)}")
        
        # Set up automatic updates
        self.setup_bindings()
        
    def setup_ui(self):
        """Create and arrange all UI components"""
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Plot frame (top)
        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Matplotlib canvas
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_frame)
        self.toolbar.update()
        
        # Control frame (bottom)
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Left panel - Line management
        line_frame = ttk.LabelFrame(control_frame, text="Графики", padding=10)
        line_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Button(line_frame, text="Загрузить данные", command=self.load_line_from_file).pack(fill=tk.X, pady=2)
        ttk.Button(line_frame, text="Загрузить карту", command=self.load_map_image).pack(fill=tk.X, pady=2)
        
        self.line_selector = ttk.Combobox(line_frame, state="readonly")
        self.line_selector.pack(fill=tk.X, pady=2)
        
        ttk.Button(line_frame, text="Удалить линию", command=self.remove_selected_line).pack(fill=tk.X, pady=2)
        
        # Middle panel - Line settings
        settings_frame = ttk.LabelFrame(control_frame, text="Настройки", padding=10)
        settings_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Settings widgets
        ttk.Label(settings_frame, text="Имя:").grid(row=0, column=0, sticky=tk.W)
        self.line_label = ttk.Entry(settings_frame)
        self.line_label.grid(row=0, column=1, sticky=tk.EW)
        
        ttk.Label(settings_frame, text="Ширина:").grid(row=1, column=0, sticky=tk.W)
        self.line_width = tk.Scale(settings_frame, from_=1, to=10, orient=tk.HORIZONTAL)
        self.line_width.grid(row=1, column=1, sticky=tk.EW)
        
        ttk.Label(settings_frame, text="Цвет:").grid(row=2, column=0, sticky=tk.W)
        self.line_color = ttk.Combobox(settings_frame,
                                        values=['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'black', 'magenta', 'purple' ])
        self.line_color.grid(row=2, column=1, sticky=tk.EW)
        
        ttk.Label(settings_frame, text="Стиль:").grid(row=3, column=0, sticky=tk.W)
        self.line_style = ttk.Combobox(settings_frame, values=['-', '--', '-.', ':'])
        self.line_style.grid(row=3, column=1, sticky=tk.EW)

        ttk.Label(settings_frame, text="Цвет маркеров:").grid(row=0, column=3, sticky=tk.W)
        self.marker_color = ttk.Combobox(settings_frame,
                                         values=['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'black', 'magenta', 'purple' ])
        self.marker_color.grid(row=0, column=4, sticky=tk.EW)

        ttk.Label(settings_frame, text="Размер маркеров:").grid(row=1, column=3, sticky=tk.W)
        self.marker_size = tk.Scale(settings_frame, from_=0, to=10, orient=tk.HORIZONTAL)
        self.marker_size.grid(row=1, column=4, sticky=tk.W)
    

        # Set default values
        self.set_default_settings()
        
    def setup_bindings(self):
        """Set up automatic update bindings"""
        self.line_selector.bind("<<ComboboxSelected>>", lambda e: (self.select_line(), self.update_plot()))
        
        # Bind all settings widgets to auto-update
        for widget in [self.line_width, self.marker_size]:
            widget.configure(command=self.on_settings_change)
            
        for widget in [self.line_label, self.line_color, self.line_style, self.marker_color]:
            widget.bind('<KeyRelease>', lambda e: self.on_settings_change())
            widget.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
            
    def set_default_settings(self):
        """Set default values for all settings widgets"""
        self.line_label.insert(0, "")
        self.line_width.set(2)
        self.line_color.set('blue')
        self.line_style.set(':')
        self.marker_size.set(0)
        self.marker_color.set('red')
        
    def on_settings_change(self, *args):
        """Handle any setting change"""
        if self.current_line_id:
            self.apply_settings()
            self.update_plot()
    
    def load_line_from_file(self):            
        """Load plot data from a tab-separated .txt file"""
        file_path = filedialog.askopenfilename(title="Выберите файл с данными", filetypes=[("Файлы *.txt", "*.txt")])        
        if not file_path:  return
        try:
            X = []; Y = []

            with open(file_path, 'r') as file:
                lines = readTxtTable(file)
                for x, y, *_ in lines:
                    X.append(x)
                    Y.append(y)

            # Create a new line with the loaded data
            line_id = self.plot_manager.add_line(X, Y)
            self.active_line_ids.append(line_id)
            self.update_line_selector()
            self.update_plot()
            
            # Set the label to the filename
            self.line_label.delete(0, tk.END)
            self.line_label.insert(0, f' График:{line_id}')
            self.apply_settings()
                
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалост загрузить данные: {str(e)}")

    def load_map_image(self):
        """Load background image from .png, .jpg file"""
        file_path = filedialog.askopenfilename(title="Выбрать карту", filetypes=[("Files", "*.*"),
                                                                                 ("PNG files", "*.png"),
                                                                                 ("JPG files", "*.jpg"),
                                                                                 ("JPEG files", "*.jpeg")])
        if not file_path: return
        try:                  
            self.plot_manager.redraw_map(file_path)  
        except Exception as e: messagebox.showerror("Error", f"Не удалось загрузить карту:\n{str(e)}")
        
        self.update_plot()

    def update_line_selector(self):
        """Update the line selector combobox with current lines"""
        lines = [f"График:{line_id}" for line_id in self.active_line_ids]
        self.line_selector['values'] = lines
        if lines:
            self.line_selector.current(0)
            self.select_line()
        else:
            self.line_selector.set('')
            self.current_line_id = None
        
    def select_line(self):
        """Select a line to modify its settings"""
        selection = self.line_selector.get()
        if selection:
            line_id = int(selection.split(':')[-1])
            self.current_line_id = line_id
            settings = self.plot_manager.lines[line_id]['settings']
            
            # Update UI with selected line's settings
            self.line_label.delete(0, tk.END)
            self.line_label.insert(0, settings['label'])
            self.line_width.set(settings['line_width'])
            self.line_color.set(settings['line_color'])
            self.line_style.set(settings['line_style'])
            self.marker_size.set(settings['marker_size'])
            self.marker_color.set(settings['marker_color'])
        
    def remove_selected_line(self):
        """Remove the currently selected line"""
        if self.current_line_id:
            self.plot_manager.remove_line(self.current_line_id)
            self.active_line_ids.remove(self.current_line_id)
            self.update_line_selector()
            self.update_plot()
        
    def apply_settings(self):
        """Apply current UI settings to selected line"""
        if self.current_line_id:
            settings = {
                'line_width': self.line_width.get(),
                'line_color': self.line_color.get(),
                'line_style': self.line_style.get(),
                'marker_size': self.marker_size.get(),
                'marker_color': self.marker_color.get(),
                'label': self.line_label.get()
            }
            self.plot_manager.update_line_settings(self.current_line_id, settings)
        
    def update_plot(self):
        """Update the plot display"""
        self.plot_manager.redraw_plot()
        self.plot_manager.redraw_map()
        self.canvas.draw_idle()  # More efficient than draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PlotApp(root)
    root.mainloop()