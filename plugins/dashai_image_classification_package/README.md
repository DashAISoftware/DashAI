# **Image Classification Package**

This package include all the necessary components (Task, Models, Dataloader) to perform image classification task.

## **Task**

**ImageClassificationTask**

The task of this package is to perform image classification. The task is defined in the `image_classification_task.py` file. The task is to classify the images into different classes. The task is defined as a class `ImageClassificationTask` which is inherited from the `BaseTask`.

## **Dataloader**

**ImageDataLoader**

This module is a dataloader for the images. The module is defined in the `image_dataloader.py` file. The module is defined as a class `ImageDataLoader` which is inherited from the `BaseDataLoader`. The module uses the `load_dataset` method from the library `datasets` to load the dataset.

## **Models**

**BasicFinetunnedModels**

This module is a image classification model which uses the pre-trained models from the `torchvision.models` and finetunes them on the given dataset. The module is defined in the `basic_finetunned_models.py` file. The module is defined as a class `BasicFinetunnedModels` which is inherited from the `ImageClassificationModel`.

The pretrained models available are:

- resnet18
- resnet34
- resnext50_32x4d
- vgg16
- maxvit_t
- densenet121
- efficientnet_b0
- googlenet
- mnasnet0_5
- mobilenet_v2
- regnet_x_16gf
