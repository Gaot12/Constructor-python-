import tkinter as tk
from tkinter import simpledialog
import math
import pymunk
from pymunk.vec2d import Vec2d
import matplotlib.path as mpath
from shapely.geometry import Polygon


class OnlineConstructor:
    def __init__(self, root):
        self.root = root
        self.root.title("Онлайн Конструктор")

        # Список для хранения фигур
        self.shapes = []

        # Создайте переменную для хранения выбранного типа фигуры (по умолчанию - прямоугольник)
        self.selected_shape_type = tk.StringVar(value="rectangle")

        # Создайте фрейм для интерфейса
        self.interface_frame = tk.Frame(self.root, width=200)
        self.interface_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False)

        # Кнопки для выбора типа фигуры
        shape_buttons = tk.Frame(self.interface_frame)
        tk.Radiobutton(
            shape_buttons,
            text="Прямоугольник",
            variable=self.selected_shape_type,
            value="rectangle",
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            shape_buttons,
            text="Круг",
            variable=self.selected_shape_type,
            value="circle",
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            shape_buttons,
            text="Треугольник",
            variable=self.selected_shape_type,
            value="triangle",
        ).pack(side=tk.LEFT)
        tk.Radiobutton(
            shape_buttons,
            text="Шестерёнка",
            variable=self.selected_shape_type,
            value="gear",
        ).pack(side=tk.LEFT)  # Добавили опцию "Шестерёнка"
        shape_buttons.pack()

        self.radius_label = tk.Label(self.interface_frame, text="Радиус шестерёнки:")
        self.radius_label.pack(pady=(20, 0))
        self.radius_entry = tk.Entry(self.interface_frame)
        self.radius_entry.insert(0, "50")
        self.radius_entry.pack()

        # Кнопка для создания новой фигуры
        self.create_button = tk.Button(self.interface_frame, text="Создать фигуру", command=self.create_shape)
        self.create_button.pack(fill=tk.Y, pady=50)

        # Кнопка для сворачивания/разворачивания интерфейса
        self.toggle_interface_button = tk.Button(self.root, text="Свернуть", command=self.toggle_interface)
        self.toggle_interface_button.pack(side=tk.RIGHT)

        # Холст для отображения фигур
        self.canvas = tk.Canvas(self.root, width=600, height=400, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Привязка событий мыши для перемещения и вращения фигур
        self.canvas.bind("<B1-Motion>", self.move_shape)
        self.canvas.bind("<Button-1>", self.select_shape)
        self.canvas.bind("<ButtonRelease-1>", self.release_button)

        self.canvas.bind("<B3-Motion>", self.move_or_rotate_shape)
        self.canvas.bind("<Button-3>", self.rotate_shape)
        self.canvas.bind("<ButtonRelease-3>", self.release_button)

        # Флаги для перемещения и вращения фигуры
        self.selected_shape = None
        self.last_x, self.last_y = 0, 0

        # Флаг для отслеживания состояния интерфейса
        self.interface_hidden = False

        self.tag_counter = 1
        self.tag_map = {}
        self.tag_items = {}

        # Физический мир
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # Гравитация отсутствует

        # Словарь для хранения тел (шестерёнок) и соответствующих им фигур на холсте
        self.bodies_shapes = {}

        self.rotated_shapes = {}

        # Доп параметры для шестерёнки
        self.is_rotating = False
        self.collision_flag = False

    def toggle_interface(self):
        # Свернуть/развернуть интерфейс
        if self.interface_hidden:
            self.root.geometry("400x400")  # Свернуть интерфейс
            self.toggle_interface_button.config(text="Развернуть")
            self.interface_frame.pack_forget()
        else:
            self.root.geometry("800x400")  # Развернуть интерфейс
            self.toggle_interface_button.config(text="Свернуть")
            self.interface_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.interface_hidden = not self.interface_hidden

    def create_gear(self, x, y):
        default_radius = 50
        default_teeth = 10
        default_tooth_height = 20
        modul = 4

        radius_value = self.radius_entry.get()
        if not radius_value.isdigit() or int(radius_value) < 0 or int(radius_value) > 100:
            radius = default_radius
        elif int(radius_value) < 20:
            radius = 20
        elif int(radius_value) > 100:
            radius = 100
        else:
            radius = int(radius_value)

        teeth = radius // modul
        tooth_height = default_tooth_height

        # Создание шестерёнки с заданными параметрами
        gear_id = self.create_gear_with_params(x, y, radius, teeth, tooth_height, 0)

        return gear_id

    def create_gear_with_params(self, x, y, radius, teeth, tooth_height, angle):
        points = []

        for i in range(teeth):

            gear_angle = i * 2 * math.pi / teeth + angle
            x_i = x + radius * math.cos(gear_angle)
            y_i = y + radius * math.sin(gear_angle)
            points.append(Vec2d(x_i, y_i))

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + radius * math.cos(gear_angle)
            y_i = y + radius * math.sin(gear_angle)
            points.append(Vec2d(x_i, y_i))

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + (radius + tooth_height) * math.cos(gear_angle)
            y_i = y + (radius + tooth_height) * math.sin(gear_angle)
            points.append(Vec2d(x_i, y_i))

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + (radius + tooth_height) * math.cos(gear_angle)
            y_i = y + (radius + tooth_height) * math.sin(gear_angle)
            points.append(Vec2d(x_i, y_i))

            # Создание отверстия в центре шестеренки
        hole_points = []
        hole_radius = radius // 3
        for i in range(30):  # Увеличьте количество точек для более гладкого круга
            angle = i * 2 * math.pi / 30
            x_i = x + hole_radius * math.cos(angle)
            y_i = y + hole_radius * math.sin(angle)
            hole_points.append(Vec2d(x_i, y_i))

        gear_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        gear_body.position = Vec2d(x, y)
        gear_shape = pymunk.Poly(gear_body, points)
        hole_shape = pymunk.Poly(gear_body, hole_points)
        gear_shape.friction = 0.8
        gear_shape.collision_type = 1
        self.space.add(gear_body, gear_shape, hole_shape)

        gear_points = [int(coord) for point in points for coord in point]
        hole_points = [int(coord) for point in hole_points for coord in point]

        # Создание главной фигуры как овального тега
        gear_id = self.tag_counter

        self.tag_counter += 1

        # Добавление полигона gear_points с тегом main_figure_id
        g1 = self.canvas.create_polygon(*gear_points, fill="orange", outline="black", tags=gear_id)

        # Добавление полигона hole_points с тегом main_figure_id
        g2 = self.canvas.create_polygon(*hole_points, fill="white", outline="black", tags=gear_id)

        self.tag_map[g1] = gear_id
        self.tag_map[g2] = gear_id
        self.tag_items[gear_id] = (g1, g2)

        self.bodies_shapes[g1] = {"gear_body": gear_body, "params": [radius, teeth, tooth_height]}

        return g1

    def create_shape(self):
        # Определите выбранный тип фигуры
        shape_type = self.selected_shape_type.get()
        shape = None

        if shape_type == "rectangle":
            # Создание нового прямоугольника
            shape = self.canvas.create_rectangle(100, 100, 200, 200, fill="blue")
        elif shape_type == "circle":
            # Создание нового круга
            shape = self.canvas.create_oval(100, 100, 200, 200, fill="red")
        elif shape_type == "triangle":
            # Создание нового треугольника
            shape = self.canvas.create_polygon(100, 100, 150, 50, 200, 100, fill="green")
        elif shape_type == "gear":
            # Создание новой шестерёнки
            shape = self.create_gear(150, 150)  # Используем угол 0 при создании
        self.shapes.append(shape)

    def select_shape(self, event):
        # Выбор фигуры для перемещения или вращения
        shape = self.canvas.find_closest(event.x, event.y)
        if shape:
            shape_coords = self.canvas.coords(shape[0])
            vertices = [
                (shape_coords[i], shape_coords[i + 1])
                for i in range(0, len(shape_coords), 2)
            ]
            path = mpath.Path(vertices)
            if path.contains_point((event.x, event.y)):
                self.selected_shape = shape[0]
                self.last_x, self.last_y = event.x, event.y

    def move_or_rotate_shape(self, event):
        # Перемещение или вращение выбранной фигуры
        if self.selected_shape:
            shape_type = self.selected_shape_type.get()
            if shape_type == "gear":
                if event.state & 0x0002:  # Проверка, зажата ли правая кнопка мыши - не работает проверка
                    self.rotate_shape(event)
                else:
                    self.move_shape(event)
            else:
                self.move_shape(event)

            # Проверка наличия столкновения с другими шестерёнками
            self.check_collision()

    def rotate_shape(self, event):
        self.is_rotating = True
        # Выбор фигуры для перемещения или вращения
        self.select_shape(event)
        angle = 0.01
        self.rotated_shapes = {self.selected_shape: 1}
        self.canvas.itemconfig(self.selected_shape, fill="red")

        def rotate(angle):
            if self.is_rotating:
                # Обновляем позицию физического тела шестерёнки перед вращением
                self.bodies_shapes[self.selected_shape]["gear_body"].angle += angle
                print(self.bodies_shapes[self.selected_shape]["gear_body"].angle)
                self.canvas.coords(self.selected_shape, *self.create_gear_points(self.selected_shape))
                self.space.step(0.01)
                self.check_collision()
                self.root.after(10, rotate, angle)  # Повторяем через 10 миллисекунд
            else:
                self.collision_flag = False
        rotate(angle)  # Запускаем цикл обновления

    def stop_rotation(self, event):
        self.is_rotating = False  # останавливаем вращение
        self.selected_shape = None

    def create_gear_points(self, shape_id, _angle=None):
        gear_body = self.bodies_shapes[shape_id]["gear_body"]
        params = self.bodies_shapes[shape_id]["params"]
        x, y = gear_body.position
        radius = params[0]
        teeth = params[1]
        tooth_height = params[2]
        print(gear_body.angle, shape_id)
        angle = gear_body.angle if not _angle else gear_body.angle + _angle

        points = []
        for i in range(teeth):
            gear_angle = i * 2 * math.pi / teeth + angle
            x_i = x + radius * math.cos(gear_angle)
            y_i = y + radius * math.sin(gear_angle)
            points.append(x_i)
            points.append(y_i)

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + radius * math.cos(gear_angle)
            y_i = y + radius * math.sin(gear_angle)
            points.append(x_i)
            points.append(y_i)

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + (radius + tooth_height) * math.cos(gear_angle)
            y_i = y + (radius + tooth_height) * math.sin(gear_angle)
            points.append(x_i)
            points.append(y_i)

            gear_angle += (math.pi / teeth) * 0.5
            x_i = x + (radius + tooth_height) * math.cos(gear_angle)
            y_i = y + (radius + tooth_height) * math.sin(gear_angle)
            points.append(x_i)
            points.append(y_i)

        return points

    def move_shape(self, event):
        # Перемещение выбранной фигуры
        if self.selected_shape:
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            tag = self.tag_map[self.selected_shape]
            all_items = self.tag_items[tag]
            for item in all_items:
                self.canvas.move(item, dx, dy)
            self.last_x, self.last_y = event.x, event.y
            if self.selected_shape_type.get() == "gear":
                # Обновление позиции тела шестерёнки в физическом мире
                if self.selected_shape in self.bodies_shapes:
                    self.bodies_shapes[self.selected_shape]["gear_body"].position = Vec2d(event.x, event.y)

    def _check_shape_collision(self, shape_id, current_shape):
        shape_coords1 = self.canvas.coords(current_shape)
        shape_coords2 = self.create_gear_points(shape_id)
        vertices1 = [
            (shape_coords1[i], shape_coords1[i + 1])
            for i in range(0, len(shape_coords1), 2)
        ]
        vertices2 = [
            (shape_coords2[i], shape_coords2[i + 1])
            for i in range(0, len(shape_coords2), 2)
        ]
        polygon1 = Polygon(vertices1)
        polygon2 = Polygon(vertices2)

        return polygon1.intersects(polygon2)

    def check_collision(self):
        # Проверка столкновений шестерёнок
        for shape_id in self.shapes:
            shape_type = self.canvas.type(shape_id)
            if shape_type == "polygon" and shape_id != self.selected_shape:
                if self._check_shape_collision(shape_id, self.selected_shape):
                    if shape_id not in self.rotated_shapes:
                        self.rotated_shapes[shape_id] = len(self.rotated_shapes) + 1
                    self.collision_flag = True
                    t = self.bodies_shapes[self.selected_shape]["params"][1]
                    self.handle_collision(shape_id, True, 0.01, t)
                else:
                    self.collision_flag = False

    def handle_collision(self, collided_shape, flag, v, t_main):
        t_collided = self.bodies_shapes[collided_shape]["params"][1]
        dif = t_collided / t_main
        coff = 1 if dif < 1 else 1
        angle = -(1 / (t_collided / t_main)) * v * coff if flag else -(1 / (t_collided / t_main)) * v * coff

        def rotate(angle):
            if self.collision_flag:
                # Обновляем позицию физического тела шестерёнки перед вращением
                self.bodies_shapes[collided_shape]["gear_body"].angle += angle

                self.canvas.coords(collided_shape, *self.create_gear_points(collided_shape, angle))
                self.space.step(0.01)
                self.get_collided_gears(collided_shape, flag, angle)
                self.root.after(10, rotate, angle)  # Повторяем через 10 миллисекунд
        rotate(angle)  # Запускаем цикл обновления

    def get_collided_gears(self, collided_shape, flag, angle):
        for shape_id in self.shapes:
            collision = False
            shape_type = self.canvas.type(shape_id)
            if shape_type == "polygon":
                if shape_id not in self.rotated_shapes:
                    collision = self._check_shape_collision(shape_id, collided_shape)
                else:
                    if self.rotated_shapes[shape_id] > self.rotated_shapes[collided_shape]:
                        collision = self._check_shape_collision(shape_id, collided_shape)
                if collision:
                    if shape_id not in self.rotated_shapes:
                        self.rotated_shapes[shape_id] = len(self.rotated_shapes) + 1
                    self.collision_flag = True
                    t = self.bodies_shapes[collided_shape]["params"][1]
                    self.handle_collision(shape_id, not flag, angle, t)

    def release_button(self, event):

        bbox = self.canvas.bbox(self.selected_shape)
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2

        new_position = Vec2d(center_x, center_y)
        self.bodies_shapes[self.selected_shape]["gear_body"].position = new_position
        self.canvas.itemconfig(self.selected_shape, fill="orange")

        # Отпускание кнопки мыши
        self.selected_shape = None
        self.is_rotating = False

    def on_closing(self):
        # Метод вызывается при закрытии окна
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = OnlineConstructor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.geometry("800x400")
    root.mainloop()