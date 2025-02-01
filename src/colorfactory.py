# This class is responsible for analizing the pixel colors and calculate the colors to broadcast.
# It also contains the LedStrips objects and can return, read and write their colors.
# The horizontal_count indicates the amount of average colors to calculate for the top and bottom border of the screen.
# The vertical_count indicates the amount of average colors to calculate for the left and right border of the screen.

import numpy as np
import cv2
from ledstrip import LedStrip
from utils import get_minecraft_health

class ColorFactory:
    # only used for debugging purposes, will draw the average colors but will slow down the average FPS
    draw_squares = False

    def __init__(self, horizontal_count: int, vertical_count: int, mode: str = ""):
        self.horizontal_count = horizontal_count
        self.vertical_count = vertical_count
        self.mode = mode
        if mode == "MINECRAFT": 
            from yolo_onnxruntime import YOLO_ONNXRuntime_Detect       
            from utils import get_minecraft_health 
            self.searching_health_bar = True
            self.healthbar_box = np.array([])
            print("Importing YOLO models..")
            self.yolo4healthbar = YOLO_ONNXRuntime_Detect(device_type="CPU", 
                                   model_type="FP32", 
                                   model_path="./yolov11_models/healthbar_480480/simplify_optimize.onnx",
                                   class_num=1,
                                   nms_threshold=0.5,
                                   confidence_threshold=0.4,
                                   inputs_shape=(480, 480)
                                   )
            self.yolo4hearts = YOLO_ONNXRuntime_Detect(device_type="CPU", 
                                        model_type="FP32", 
                                        model_path="./yolov11_models/hearts_500_320320/simplify_optimize.onnx",
                                        class_num=3,
                                        nms_threshold=0.5,
                                        confidence_threshold=0.1,
                                        inputs_shape=(320, 320))

        # don't change these id's
        self.led_strips = {
            "left": LedStrip(1, vertical_count),
            "top": LedStrip(2, horizontal_count),
            "right": LedStrip(3, vertical_count),
            "bottom": LedStrip(4, horizontal_count),
            "full_screen": LedStrip(5, 1),
        }
        ids = [self.led_strips[k].id for k in self.led_strips.keys()]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Every id of each LedStrip must be unique.")
        elif 0 in ids:
            raise ValueError(f"Id '0' cannot be used for initiating a LedStrip. It's reserved for the transmitter.")

    def get_average_color(self, x: int, y: float, h_size: int, v_size: int, image: np.ndarray) -> np.ndarray:
        # Define square's start and end points
        start_point = (int(x - v_size / 2), int(y - h_size / 2))
        end_point = (int(x + v_size / 2), int(y + h_size / 2))
        # Ensure the region is within the image bounds
        start_point = (max(start_point[0], 0), max(start_point[1], 0))
        end_point = (min(end_point[0], image.shape[1]), min(end_point[1], image.shape[0]))

        # Calculate the average color in this region from the original image
        region = image[start_point[1] : end_point[1], start_point[0] : end_point[0]]

        if region.size > 0:  # Avoid empty regions
            average_color = region.mean(axis=(0, 1)).astype(int)
        else:
            average_color = np.zeros((1, 3))  # Fallback if region is empty

        if ColorFactory.draw_squares:
            cv2.rectangle(image, start_point, end_point, tuple(map(int, average_color)), -1)

        # Return the average color
        return average_color
    
    def average_colors(self, image: np.ndarray) -> tuple[np.ndarray, list[LedStrip]]:
        image = cv2.resize(image, (100, 100), interpolation=cv2.INTER_AREA)
        height, width = image.shape[:2]

        square_size_horizontal = int(width / self.horizontal_count)
        square_size_vertical = int(height / self.vertical_count)

        for index, i in enumerate(
            np.linspace(square_size_horizontal / 2, width - square_size_horizontal / 2, self.horizontal_count)
        ):
            x = int(i)

            c = self.get_average_color(x, square_size_horizontal / 2, int(height / 50), square_size_horizontal, image)
            self.led_strips["top"].update_light(index, c)

            c = self.get_average_color(
                x, height - square_size_horizontal / 2, int(height / 50), square_size_horizontal, image
            )
            self.led_strips["bottom"].update_light(index, c)

        for index, i in enumerate(
            np.linspace(square_size_vertical / 2, height - square_size_vertical / 2, self.vertical_count)
        ):
            y = int(i)

            c = self.get_average_color(square_size_vertical / 2, y, square_size_vertical, int(width / 50), image)
            self.led_strips["left"].update_light(index, c)

            c = self.get_average_color(width - square_size_vertical / 2, y, square_size_vertical, int(width / 50), image)
            self.led_strips["right"].update_light(index, c)

        self.led_strips["full_screen"].update_light(0, image.mean(axis=(0, 1)).astype(int))

        return image, self.get_strips()
    
    def minecraft_health(self, image: np.ndarray) -> tuple[np.ndarray, list[LedStrip]]:
        resized_image = cv2.resize(image, (480, 480), interpolation=cv2.INTER_AREA)
        if self.searching_health_bar:
            self.yolo4healthbar.pre_process(resized_image)
            self.yolo4healthbar.process()
            best_healthbar = self.yolo4healthbar.get_best_boxes(1, resized_image)
            if best_healthbar.shape[0] == 1:
                self.searching_health_bar = False
                self.healthbar_box = best_healthbar
                '''x,y,x2,y2 = map(int,best_healthbar[0][:4])
                cv2.rectangle(resized_image, (x,y), (x2,y2), (255,0,0), 1)'''

        else:
            x1, y1, x2, y2 = map(int, self.healthbar_box[0][:4])
            old_h, old_w, _ = image.shape
            new_h, new_w, _ = resized_image.shape
            x_factor = old_w/new_w
            y_factor = old_h/new_h
            x1, y1, x2, y2 = map(int, [x1*x_factor,y1*y_factor,x2*x_factor,y2*y_factor])
            half_width = int((x2 - x1)/2)
            #cv2.rectangle(image, (int(x1*x_factor),int(y1*y_factor)), (int(x2*x_factor),int(y2*y_factor)), (255,0,0), 1)
            image = image[y2-half_width*2-10:y2+10, x1-10:x2+10]
            self.yolo4hearts.pre_process(image)
            self.yolo4hearts.process()
            best_hearts = self.yolo4hearts.get_best_boxes(10, image)
            if best_hearts.shape[0] == 10:
                health = get_minecraft_health(best_hearts)
                red = int(255 * (1 - health / 10))
                green = int(255 * (health / 10))
                color = np.array([0, green, red], dtype=np.uint8)
                self.set_strips(color)
                '''for heart in best_hearts:
                    x,y,x2,y2 = map(int,heart[:4])
                    detected_class = int(heart[5])
                    color = (255,255,255)
                    match detected_class:
                        case 0:
                            color = (0,165,255)
                        case 1:
                            color = (0,0,255)
                        case 2:
                            color = (0,255,0)
                        case _:
                            print("Unknown class")
                            # Default case if none of the above match
                    cv2.rectangle(image, (x,y), (x2,y2), tuple(map(int,color)), 1)'''

            else:
                print("Search new healthbar")
                self.searching_health_bar = True
                self.healthbar_box = np.array([])
        
        return image, self.get_strips()


    def calculate_colors(self, image: np.ndarray) -> tuple[np.ndarray, list[LedStrip]]:
        match self.mode:
            case "MINECRAFT":
                return self.minecraft_health(image)
            case "AVERAGE":
                return self.average_colors(image)
            case _:
                print("No correct mode was set in config.ini!")
        
        return image, self.get_strips()

    def get_strips(self) -> list[LedStrip]:
        return [
            self.led_strips["left"],
            self.led_strips["right"],
            self.led_strips["top"],
            self.led_strips["bottom"],
            self.led_strips["full_screen"],
        ]

    def test_strips(self) -> list[LedStrip]:
        for strip in self.get_strips():
            strip.set_next_color()
        return self.get_strips()

    def set_strips(self, color: np.array) -> list[LedStrip]:
        for strip in self.get_strips():
            strip.set_lights(color)
        return self.get_strips()
