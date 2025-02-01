import onnxruntime
from utils import draw_result, letterbox, xywh2xyxy, nms, scale_boxes
import os
import numpy as np
import cv2


'''
description: onnxruntime inference class for YOLO algorithm
'''
class YOLO_ONNXRuntime():
    '''
    description:            construction method
    param {*} self          instance of class
    param {str} device_type device type
    param {str} model_type  model type
    param {str} model_path  model path
    return {*}
    '''    
    def __init__(self, device_type:str, model_type:str, model_path:str, class_num:int, nms_threshold:float, confidence_threshold:float, inputs_shape:tuple[int, int]) -> None:
        self.class_num = class_num
        self.nms_threshold = nms_threshold
        self.confidence_threshold = confidence_threshold
        self.inputs_shape = inputs_shape

        assert os.path.exists(model_path), 'model not exists!'
        assert device_type in ['CPU', 'GPU'], 'unsupported device type!'
        if device_type == 'CPU':
            self.onnx_session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        elif device_type == 'GPU':
            self.onnx_session = onnxruntime.InferenceSession(model_path, providers=['CUDAExecutionProvider'])
        self.model_type = model_type
         
        self.inputs_name = []
        for node in self.onnx_session.get_inputs(): 
            self.inputs_name.append(node.name)
        self.outputs_name = []
        for node in self.onnx_session.get_outputs():
            self.outputs_name.append(node.name)
        self.inputs = {}
    
    def process(self) -> None:
        self.outputs = self.onnx_session.run(None, self.inputs)

'''
description: onnxruntime inference class for the YOLO classfiy algorithm
'''
class YOLO_ONNXRuntime_Classify(YOLO_ONNXRuntime):       
    def pre_process(self, image) -> None:
        if image.shape[1] > image.shape[0]:
            image = cv2.resize(image, (self.inputs_shape[0]*image.shape[1]//image.shape[0], self.inputs_shape[0]))
        else:
            image = cv2.resize(image, (self.inputs_shape[1], self.inputs_shape[1]*image.shape[0]//image.shape[1]))
        crop_size = min(image.shape[0], image.shape[1])
        left = (image.shape[1] - crop_size) // 2
        top = (image.shape[0] - crop_size) // 2
        crop_image = image[top:(top+crop_size), left:(left+crop_size), ...]
        input = cv2.resize(crop_image, self.inputs_shape)
        input = input / 255.0
            
        input = input[:, :, ::-1].transpose(2, 0, 1)  #BGR2RGB and HWC2CHW
        if self.model_type == 'FP32' or self.model_type == 'INT8':
            input = np.expand_dims(input, axis=0).astype(dtype=np.float32)
        elif self.model_type == 'FP16':
            input = np.expand_dims(input, axis=0).astype(dtype=np.float16)
            
        for name in self.inputs_name:
            self.inputs[name] = input
            
    def post_process(self) -> None:
        output = np.squeeze(self.outputs).astype(dtype=np.float32)
        print("class:", np.argmax(output), " scores:", np.max(output))


'''
description: onnxruntime inference class for the YOLO detection algorithm
'''
class YOLO_ONNXRuntime_Detect(YOLO_ONNXRuntime):
    def pre_process(self, image) -> None:
        input = letterbox(image, self.inputs_shape)
        input = input[:, :, ::-1].transpose(2, 0, 1)  #BGR2RGB and HWC2CHW
        input = input / 255.0
        if self.model_type == 'FP32' or self.model_type == 'INT8':
            input = np.expand_dims(input, axis=0).astype(dtype=np.float32)
        elif self.model_type == 'FP16':
            input = np.expand_dims(input, axis=0).astype(dtype=np.float16)
        for name in self.inputs_name:
            self.inputs[name] = input

    def get_best_boxes(self, n: int, image: np.ndarray, write_image=False) -> np.ndarray:
        output = np.squeeze(self.outputs[0]).astype(dtype=np.float32)
        boxes = []
        scores = []
        class_ids = []

        output = output.T
        classes_scores = output[..., 4:(4 + self.class_num)]
        
        for i in range(output.shape[0]):       
            class_id = np.argmax(classes_scores[i])
            score = classes_scores[i][class_id]
            if score > self.confidence_threshold:
                boxes.append(np.concatenate([output[i, :4], np.array([score, class_id])]))
                scores.append(score)
                class_ids.append(class_id)

        if len(boxes):   
            boxes = np.array(boxes)
            scores = np.array(scores)

            boxes = xywh2xyxy(boxes)
            indices = nms(boxes, scores, self.nms_threshold) 
            
            boxes = boxes[indices]
            scores = scores[indices]
            class_ids = np.array(class_ids)[indices]

            boxes = scale_boxes(boxes, self.inputs_shape, image.shape)

            if len(boxes) >= n:
                top_indices = np.argsort(scores)[::-1][:n]  # Sort by descending confidence and get top n
                boxes = boxes[top_indices]
                scores = scores[top_indices]
                class_ids = class_ids[top_indices]

                if write_image:
                    self.result = draw_result(image, boxes)
                    cv2.imwrite("detected.jpeg", self.result)
                return boxes
            else:
                print(f"Not enough boxes found: {len(boxes)} compared to requested {n}")
        else:
            print(f"Wrong number of boxes found: {0} compared to requested {n}")
            

        # Return empty array if we don't have at least `n` boxes
        return np.array([])