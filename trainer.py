from detectron2.utils.logger import setup_logger

setup_logger()

from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.config import get_cfg
from detectron2.engine import DefaultPredictor, DefaultTrainer
from detectron2 import model_zoo
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader

import os
import pickle
import cv2
import numpy as np

from utils import *

class Detector:
        def __init__(self):
                self.cfg = get_cfg()
                self.cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_X_101_32x8d_FPN_3x.yaml"))
                self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_X_101_32x8d_FPN_3x.yaml")
                
                regist_dataset()


                ## 4 Fold Training
                self.cfg.DATASETS.TRAIN = ("Example", )
                self.test_dataset = "Example"
                self.coco_test_metadata = MetadataCatalog.get(self.test_dataset)
                self.cfg.DATASETS.TEST = (self.test_dataset, )
                
                self.cfg.DATALOADER.NUM_WORKERS = 0

                
                self.cfg.SOLVER.STEPS = []
                self.cfg.SOLVER.IMS_PER_BATCH = 1
                num_gpu = 1
                bs = (num_gpu * 2)
                self.cfg.SOLVER.BASE_LR = 0.0002 * bs / 16  # pick a good LR
                self.cfg.SOLVER.MAX_ITER = 1000    # 300 iterations seems good enough for this toy dataset; you may need to train longer for a practical dataset
                self.cfg.MODEL.ANCHOR_GENERATOR.SIZES = [[16], [48], [96], [216], [480]]  # One size for each in feature map
                self.cfg.MODEL.ANCHOR_GENERATOR.ASPECT_RATIOS = [[0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 50, 60, 70]] # Three aspect ratios (same for all in feature maps)
                self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 3
                self.cfg.MODEL.DEVICE = "cuda"
                self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7

                self.cfg.OUTPUT_DIR = './Weights/instance_segmentation'
                os.makedirs(self.cfg.OUTPUT_DIR, exist_ok=True)

        def train(self):
                
                self.trainer = DefaultTrainer(self.cfg)
                self.trainer.resume_or_load(resume = False)
                self.trainer.train()
                evaluator = COCOEvaluator(self.test_dataset, self.cfg, False, output_dir = self.cfg.OUTPUT_DIR)
                val_loader = build_detection_test_loader(self.cfg, self.test_dataset)
                inference_on_dataset(self.trainer.model, val_loader, evaluator)              
        
        def Save_Prediction(self, imagePath :str, saveFolder :str, model :str):
                
                image = cv2.imread(imagePath)
                
                if not os.path.exists(saveFolder):
                        os.makedirs(saveFolder)

                self.cfg.MODEL.WEIGHTS = os.path.join(self.cfg.OUTPUT_DIR, model)
                self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7
                predictor = DefaultPredictor(self.cfg)
                predictions = predictor(image)

                viz = Visualizer(image[:, :, ::-1],
                        metadata=self.coco_test_metadata,
                        scale=0.8,
                        instance_mode=ColorMode.IMAGE_BW)
                output = viz.draw_instance_predictions(predictions["instances"].to("cpu"))
                
                result = output.get_image()[:, :, ::-1]

                cv2.imwrite(saveFolder + '/' + imagePath.split('/')[-1], result)
        
        def Save_Mask(self, imagePath :str, saveFolder :str, model :str):
                
                image = cv2.imread(imagePath)

                if not os.path.exists(saveFolder):
                        os.makedirs(saveFolder)
                
                self.cfg.MODEL.WEIGHTS = os.path.join(self.cfg.OUTPUT_DIR, model)
                predictor = DefaultPredictor(self.cfg)
                outputs = predictor(image)

                mask = outputs["instances"].to("cpu").get("pred_masks").numpy()
                binary_mask = np.zeros((mask.shape[1],mask.shape[2]))
                for i in range(mask.shape[0]):
                        binary_mask += mask[i]

                np.where(binary_mask > 0, 255, 0)

                cv2.imwrite(saveFolder + '/' + imagePath.split('/')[-1], binary_mask*255)

        def Save_Prediction_Video(self, videoPath :str, saveFolder :str, model :str):
                pass
