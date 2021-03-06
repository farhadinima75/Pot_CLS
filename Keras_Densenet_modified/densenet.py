from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.python.keras import backend
from tensorflow.python.keras.applications import imagenet_utils
from tensorflow.python.keras.engine import training
from tensorflow.python.keras.layers import VersionAwareLayers
from tensorflow.python.keras.utils import data_utils
from tensorflow.python.keras.utils import layer_utils
from tensorflow.python.lib.io import file_io
from tensorflow.python.util.tf_export import keras_export
import tensorflow 

layers = VersionAwareLayers()


def dense_block(x, blocks, name):
  """A dense block.
  Arguments:
    x: input tensor.
    blocks: integer, the number of building blocks.
    name: string, block label.
  Returns:
    Output tensor for the block.
  """
  for i in range(blocks):
    x = conv_block(x, 10, name=name + '_block' + str(i + 1))
  return x


def transition_block(x, reduction, name):
  """A transition block.
  Arguments:
    x: input tensor.
    reduction: float, compression rate at transition layers.
    name: string, block label.
  Returns:
    output tensor for the block.
  """
  bn_axis = 3 if backend.image_data_format() == 'channels_last' else 1
  x = layers.BatchNormalization(
      axis=bn_axis, epsilon=1.001e-5, name=name + '_bn')(
          x)
  x = layers.Activation('relu', name=name + '_relu')(x)
  x = layers.Conv2D(
      int(backend.int_shape(x)[bn_axis] * reduction),
      1,
      use_bias=False,
      name=name + '_conv',
      kernel_initializer='he_normal',
      kernel_regularizer = tensorflow.keras.regularizers.l2(1e-4))(x)
  #x = tensorflow.keras.layers.SpatialDropout2D(0.1)(x)
  x = layers.AveragePooling2D(2, strides=2, name=name + '_pool')(x)
  return x


def conv_block(x, growth_rate, name):
  """A building block for a dense block.
  Arguments:
    x: input tensor.
    growth_rate: float, growth rate at dense layers.
    name: string, block label.
  Returns:
    Output tensor for the block.
  """
  bn_axis = 3 if backend.image_data_format() == 'channels_last' else 1

  x1 = layers.BatchNormalization(
      axis=bn_axis, epsilon=1.001e-5, name=name + '_1_bn')(
          x)
  x1 = layers.Activation('relu', name=name + '_1_relu')(x1)
  x1 = layers.Conv2D(
      growth_rate, 3, padding='same', use_bias=False, name=name + '_2_conv',
      kernel_initializer='he_normal',
      kernel_regularizer = tensorflow.keras.regularizers.l2(1e-4))(x1)
  #x1 = tensorflow.keras.layers.SpatialDropout2D(0.1)(x1)
  x = layers.Concatenate(axis=bn_axis, name=name + '_concat')([x, x1])
  return x


def DenseNet(blocks, include_top=True, weights='imagenet', input_tensor=None, input_shape=None,
             pooling=None, classes=1000, classifier_activation='softmax'):

  # Determine proper input shape
  input_shape = imagenet_utils.obtain_input_shape(
      input_shape,
      default_size=224,
      min_size=16,
      data_format=backend.image_data_format(),
      require_flatten=include_top,
      weights=weights)

  if input_tensor is None:
    img_input = layers.Input(shape=input_shape)
  else:
    if not backend.is_keras_tensor(input_tensor):
      img_input = layers.Input(tensor=input_tensor, shape=input_shape)
    else:
      img_input = input_tensor

  bn_axis = 3 if backend.image_data_format() == 'channels_last' else 1

  x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)))(img_input)
  x = layers.Conv2D(50, 3, strides=1, use_bias=False, name='conv1/conv',
      kernel_initializer='he_normal',
      kernel_regularizer = tensorflow.keras.regularizers.l2(1e-4))(x)
  x = layers.BatchNormalization(
      axis=bn_axis, epsilon=1.001e-5, name='conv1/bn')(
          x)
  x = layers.Activation('relu', name='conv1/relu')(x)
  x = layers.ZeroPadding2D(padding=((1, 1), (1, 1)))(x)
  x = layers.MaxPooling2D(3, strides=2, name='pool1')(x)

  x = dense_block(x, blocks[0], name='conv2')
  x = transition_block(x, 1, name='pool2')
  x = dense_block(x, blocks[1], name='conv3')
  x = transition_block(x, 1, name='pool3')
  x = dense_block(x, blocks[2], name='conv4')
 # x = transition_block(x, 1, name='pool4')
  #x = dense_block(x, blocks[3], name='conv5')

  x = layers.BatchNormalization(axis=bn_axis, epsilon=1.001e-5, name='bn')(x)
  x = layers.Activation('relu', name='relu')(x)

  if include_top:
    x = layers.GlobalAveragePooling2D(name='avg_pool')(x)

    imagenet_utils.validate_activation(classifier_activation, weights)
    x = layers.Dense(classes, activation=classifier_activation,
                     name='predictions')(x)
  else:
    if pooling == 'avg':
      x = layers.GlobalAveragePooling2D(name='avg_pool')(x)
    elif pooling == 'max':
      x = layers.GlobalMaxPooling2D(name='max_pool')(x)

  # Ensure that the model takes into account
  # any potential predecessors of `input_tensor`.
  if input_tensor is not None:
    inputs = layer_utils.get_source_inputs(input_tensor)
  else:
    inputs = img_input

  # Create model.
  if blocks == [6, 12, 24, 16]:
    model = training.Model(inputs, x, name='densenet121')
  elif blocks == [6, 12, 32, 32]:
    model = training.Model(inputs, x, name='densenet169')
  elif blocks == [6, 12, 48, 32]:
    model = training.Model(inputs, x, name='densenet201')
  else:
    model = training.Model(inputs, x, name='densenet')

  return model


@keras_export('keras.applications.densenet.DenseNet121',
              'keras.applications.DenseNet121')
def DenseNet121(block = [4, 8, 10, 12],
                include_top=True,
                weights='imagenet',
                input_tensor=None,
                input_shape=None,
                pooling=None,
                classes=1000):
  """Instantiates the Densenet121 architecture."""
  return DenseNet(block, include_top, weights, input_tensor,
                  input_shape, pooling, classes)


@keras_export('keras.applications.densenet.DenseNet169',
              'keras.applications.DenseNet169')
def DenseNet169(include_top=True,
                weights='imagenet',
                input_tensor=None,
                input_shape=None,
                pooling=None,
                classes=1000):
  """Instantiates the Densenet169 architecture."""
  return DenseNet([6, 12, 32, 32], include_top, weights, input_tensor,
                  input_shape, pooling, classes)


@keras_export('keras.applications.densenet.DenseNet201',
              'keras.applications.DenseNet201')
def DenseNet201(include_top=True,
                weights='imagenet',
                input_tensor=None,
                input_shape=None,
                pooling=None,
                classes=1000):
  """Instantiates the Densenet201 architecture."""
  return DenseNet([6, 12, 48, 32], include_top, weights, input_tensor,
                  input_shape, pooling, classes)


@keras_export('keras.applications.densenet.preprocess_input')
def preprocess_input(x, data_format=None):
  return imagenet_utils.preprocess_input(
      x, data_format=data_format, mode='torch')


@keras_export('keras.applications.densenet.decode_predictions')
def decode_predictions(preds, top=5):
  return imagenet_utils.decode_predictions(preds, top=top)


preprocess_input.__doc__ = imagenet_utils.PREPROCESS_INPUT_DOC.format(
    mode='',
    ret=imagenet_utils.PREPROCESS_INPUT_RET_DOC_TORCH,
    error=imagenet_utils.PREPROCESS_INPUT_ERROR_DOC)
decode_predictions.__doc__ = imagenet_utils.decode_predictions.__doc__

DOC = """
  Reference paper:
  - [Densely Connected Convolutional Networks]
    (https://arxiv.org/abs/1608.06993) (CVPR 2017 Best Paper Award)
  Optionally loads weights pre-trained on ImageNet.
  Note that the data format convention used by the model is
  the one specified in your Keras config at `~/.keras/keras.json`.
  Arguments:
    include_top: whether to include the fully-connected
      layer at the top of the network.
    weights: one of `None` (random initialization),
      'imagenet' (pre-training on ImageNet),
      or the path to the weights file to be loaded.
    input_tensor: optional Keras tensor (i.e. output of `layers.Input()`)
      to use as image input for the model.
    input_shape: optional shape tuple, only to be specified
      if `include_top` is False (otherwise the input shape
      has to be `(224, 224, 3)` (with `'channels_last'` data format)
      or `(3, 224, 224)` (with `'channels_first'` data format).
      It should have exactly 3 inputs channels,
      and width and height should be no smaller than 32.
      E.g. `(200, 200, 3)` would be one valid value.
    pooling: Optional pooling mode for feature extraction
      when `include_top` is `False`.
      - `None` means that the output of the model will be
          the 4D tensor output of the
          last convolutional block.
      - `avg` means that global average pooling
          will be applied to the output of the
          last convolutional block, and thus
          the output of the model will be a 2D tensor.
      - `max` means that global max pooling will
          be applied.
    classes: optional number of classes to classify images
      into, only to be specified if `include_top` is True, and
      if no `weights` argument is specified.
  Returns:
    A Keras model instance.
"""

setattr(DenseNet121, '__doc__', DenseNet121.__doc__ + DOC)
setattr(DenseNet169, '__doc__', DenseNet169.__doc__ + DOC)
setattr(DenseNet201, '__doc__', DenseNet201.__doc__ + DOC)
