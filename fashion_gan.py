# -*- coding: utf-8 -*-
"""fashion_gan.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1leTkcGQf8sS2ywqHDuSQUS27tZJoH5ET

# Import Dependencies
"""

!pip install tensorflow matplotlib tensorflow-datasets ipywidgets

#bringing in tensorflow dataset
import tensorflow_datasets as tfds
from matplotlib import pyplot as plt

pip install --upgrade tensorflow tensorflow-datasets

ds=tfds.load('fashion_mnist', split='train')

ds.as_numpy_iterator().next()['label']

type(ds)

"""# viz data & build dataset"""

import numpy as np

dataiterator = ds.as_numpy_iterator()

#getting data from pipeline
dataiterator.next()

#setup subplot formatting
fig, ax = plt.subplots(ncols=4, figsize=(20,20))
for idx in range(4):
    batch = dataiterator.next()
    ax[idx].imshow(np.squeeze(batch['image']))
    ax[idx].title.set_text(batch['label'])

def scale_images(data):
    image=data['image']
    return image/255

ds =tfds.load('fashion_mnist', split='train')
ds=ds.map(scale_images)
ds=ds.cache()
ds=ds.shuffle(60000)
ds=ds.batch(128)
ds=ds.prefetch(64)

"""# 3 build neural network

# 3.1 import modelling components
"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Dense, Flatten, Reshape, LeakyReLU, Dropout, UpSampling2D

"""# 3.2 build generator"""

def build_generator():
    model = Sequential()
    model.add(Dense(7*7*128, input_dim=128))
    model.add(LeakyReLU(0.2))
    model.add(Reshape((7,7,128)))

    #upsampling block
    model.add(UpSampling2D())
    model.add(Conv2D(128,5,padding='same'))
    model.add(LeakyReLU(0.2))

    #upsampling block 2
    model.add(UpSampling2D())
    model.add(Conv2D(128,5,padding='same'))
    model.add(LeakyReLU(0.2))

    #downsampling block
    model.add(Conv2D(128,4,padding='same'))
    model.add(LeakyReLU(0.2))

    #downsampling block 2
    model.add(Conv2D(128,4,padding='same'))
    model.add(LeakyReLU(0.2))

    #conv layer to get to one channel
    model.add(Conv2D(1,4,padding='same',activation='sigmoid'))

    return model

test_model = build_generator()

test_model.summary()

generator= build_generator()

generator.summary()

img=generator.predict(np.random.randn(4,128,1))
img

#setup subplot formatting
img = generator.predict(np.random.randn(4,128,1))
fig, ax = plt.subplots(ncols=4, figsize=(20,20))
for idx,img in enumerate(img):
    ax[idx].imshow(np.squeeze(img))
    ax[idx].title.set_text(idx)

"""# 3.3 build discriminator"""

def build_discriminator():
    model = Sequential()

    # Conv2D expects a tuple for the kernel size, so (5, 5) instead of 5
    model.add(Conv2D(32, (5, 5), input_shape=(28, 28, 1)))  #32 filters of size 5x5 , i/p shape= o/p shape = 28
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.4))

    #conv layer 2
    model.add(Conv2D(64, (5, 5)))  #32 filters of size 5x5 , i/p shape= o/p shape = 28
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.4))

    #conv layer 3
    model.add(Conv2D(128, (5, 5)))  #32 filters of size 5x5 , i/p shape= o/p shape = 28
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.4))

    #conv layer 4
    model.add(Conv2D(256, (5, 5)))  #32 filters of size 5x5 , i/p shape= o/p shape = 28
    model.add(LeakyReLU(0.2))
    model.add(Dropout(0.4))

    model.add(Flatten())
    model.add(Dropout((0.4)))
    model.add(Dense(1, activation='sigmoid'))  # 1 represents false image ie fake image

    return model

discriminator =  build_discriminator()

discriminator.summary()

discriminator.predict(img)

"""# 4 custom training loop

# 4.1 Setup losses and optimizers
"""

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy

g_opt = Adam(learning_rate = 0.0001)
d_opt = Adam(learning_rate = 0.00001)
g_loss = BinaryCrossentropy()
d_loss = BinaryCrossentropy()

"""# 4.2 build subclassed model"""

from tensorflow.keras.models import Model

# import tensorflow as tf
# class FashionGan(Model):
#     def __init__(self, generator,discriminator, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         #Create attributes for gen and disc
#         self.generator = generator
#         self.discriminator = discriminator

#     def compile(self,g_opt,d_opt,g_loss,d_loss,*args, **kwargs):
#         super().compile(*args, **kwargs)
#         #Create attributes for loss and optimizers
#         self.g_opt = g_opt
#         self.d_opt = d_opt
#         self.g_loss = g_loss
#         self.d_loss = d_loss

#     def call(self, inputs):
#         # Generate noise vectors
#         batch_size = tf.shape(inputs)[0]
#         noise = tf.random.normal((batch_size, 128))
#         # Generate fake images
#         return self.generator(noise)

#     def test_step(self, batch):
#         real_images = batch
#         fake_images = self.generator(tf.random.normal((128,128,1)),training = False)

#         #train discriminator
#         with tf.GradientTape() as d_tape:
#             #pass real and fake images to discriminator
#             yhat_real = self.discriminator(real_images, training = True)  #storing values of real images to the var
#             yhat_fake = self.discriminator(fake_images, training = True) # same for fake images
#             yhat_realfake = tf.concat([yhat_real, yhat_fake],axis=0)     # concating both

#             #create labels for real and fake images
#             y_realfake = tf.concat([tf.zeros_like(yhat_real),tf.ones_like(yhat_fake)], axis=0)  #true y values ie 0 for real images and 1 for fake images
#             #add noise to op
#             noise_real = 0.15*tf.random.uniform(tf.shape(yhat_real))
#             noise_fake = -0.15*tf.random.uniform(tf.shape(yhat_fake))
#             y_realfake += tf.concat([noise_real,noise_fake],axis=0)
#             #calculate loss
#             total_d_loss = self.d_loss(y_realfake,yhat_realfake)
#         #back propagation - nn learn
#         dgrad = d_tape.gradient(total_d_loss, self.discriminator.trainable_variables)
#         self.d_opt.apply_gradients(zip(dgrad,self.discriminator.trainable_variables)) #applying backprop

#         #train generator
#         with tf.GradientTape() as g_tape:
#             #Generate some new images
#             gen_images = self.generator(tf.random.normal((128,128,1)),training = True)
#             #Create predicted labels
#             predicted_labels = self.discriminator(gen_images, training = False)
#             #Create loss-trick to training to fake out descriminator, rewarding generator if discriminator classifies generated image as real
#             total_g_loss = self.g_loss(tf.zeros_like(predicted_labels),predicted_labels)
#         #apply backprop
#         ggrad = g_tape.gradient(total_g_loss, self.generator.trainable_variables)
#         self.g_opt.apply_gradients(zip(ggrad,self.generator.trainable_variables))
#         return {"d_loss":total_d_loss, "g_loss":total_g_loss}

import tensorflow as tf

class FashionGan(tf.keras.Model):
    def __init__(self, generator, discriminator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generator = generator
        self.discriminator = discriminator

    def compile(self, g_opt, d_opt, g_loss, d_loss, *args, **kwargs):
        super().compile(*args, **kwargs)
        self.g_opt = g_opt
        self.d_opt = d_opt
        self.g_loss = g_loss
        self.d_loss = d_loss
        # Add a dummy loss to satisfy Keras' expectations
        self.loss = lambda y_true, y_pred: tf.reduce_mean(y_pred)

    def call(self, inputs):
        batch_size = tf.shape(inputs)[0]
        noise = tf.random.normal((batch_size, 128))
        return self.generator(noise)

    def train_step(self, batch):
        real_images = batch
        batch_size = tf.shape(real_images)[0]
        noise = tf.random.normal((batch_size, 128))

        # Train discriminator
        with tf.GradientTape() as d_tape:
            fake_images = self.generator(noise, training=True)
            yhat_real = self.discriminator(real_images, training=True)
            yhat_fake = self.discriminator(fake_images, training=True)
            yhat_realfake = tf.concat([yhat_real, yhat_fake], axis=0)

            y_realfake = tf.concat([tf.zeros_like(yhat_real), tf.ones_like(yhat_fake)], axis=0)
            noise_real = 0.15 * tf.random.uniform(tf.shape(yhat_real))
            noise_fake = -0.15 * tf.random.uniform(tf.shape(yhat_fake))
            y_realfake += tf.concat([noise_real, noise_fake], axis=0)

            total_d_loss = self.d_loss(y_realfake, yhat_realfake)

        dgrad = d_tape.gradient(total_d_loss, self.discriminator.trainable_variables)
        self.d_opt.apply_gradients(zip(dgrad, self.discriminator.trainable_variables))

        # Train generator
        with tf.GradientTape() as g_tape:
            fake_images = self.generator(tf.random.normal((batch_size, 128)), training=True)
            predicted_labels = self.discriminator(fake_images, training=False)
            total_g_loss = self.g_loss(tf.zeros_like(predicted_labels), predicted_labels)

        ggrad = g_tape.gradient(total_g_loss, self.generator.trainable_variables)
        self.g_opt.apply_gradients(zip(ggrad, self.generator.trainable_variables))

        return {"d_loss": total_d_loss, "g_loss": total_g_loss}

    def test_step(self, batch):
        # Implement if needed, or return an empty dict if not needed
        return {}

fashgan = FashionGan(generator, discriminator)

fashgan.compile(g_opt,d_opt,g_loss,d_loss)

"""# 4.3 build callback"""

import os
from tensorflow.keras.preprocessing.image import array_to_img
from tensorflow.keras.callbacks import Callback

import tensorflow as tf
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.preprocessing.image import array_to_img
import os

class ModelMonitor(Callback):
    def __init__(self, num_img=3, latent_dim=128):
        self.num_img = num_img
        self.latent_dim = latent_dim

    def on_epoch_end(self, epoch, logs=None):
        random_latent_vectors = tf.random.normal((self.num_img, self.latent_dim))
        generated_images = self.model.generator(random_latent_vectors)
        generated_images = (generated_images * 0.5 + 0.5) * 255  # Denormalize
        generated_images = tf.clip_by_value(generated_images, 0, 255)
        generated_images = generated_images.numpy().astype('uint8')

        for i in range(self.num_img):
            img = array_to_img(generated_images[i])
            img.save(os.path.join('images', f'generated_img_{epoch}_{i}.png'))

import os
import tensorflow as tf
from tensorflow.keras.callbacks import Callback, ModelCheckpoint
from tensorflow.keras.preprocessing.image import array_to_img

class ModelMonitor(Callback):
    def __init__(self, num_img=3, latent_dim=128):
        self.num_img = num_img
        self.latent_dim = latent_dim

    def on_epoch_end(self, epoch, logs=None):
        random_latent_vectors = tf.random.normal((self.num_img, self.latent_dim))
        generated_images = self.model.generator(random_latent_vectors)
        generated_images = (generated_images * 0.5 + 0.5) * 255  # Denormalize
        generated_images = tf.clip_by_value(generated_images, 0, 255)
        generated_images = generated_images.numpy().astype('uint8')

        for i in range(self.num_img):
            img = array_to_img(generated_images[i])
            img.save(os.path.join('images', f'generated_img_{epoch}_{i}.png'))

# Calculate steps_per_epoch
if isinstance(ds, tf.data.Dataset):
    steps_per_epoch = ds.cardinality().numpy()
    if steps_per_epoch == tf.data.INFINITE_CARDINALITY:
        raise ValueError("Dataset is infinite. Please specify steps_per_epoch manually.")
else:
    # If ds is not a tf.data.Dataset, you need to calculate steps_per_epoch manually
    # Assuming ds is some iterable with a __len__ method:
    steps_per_epoch = len(ds)

# Calculate save frequency in terms of batches
save_freq = max(1, int(5 * steps_per_epoch))  # Save every 5 epochs, but at least every epoch

# Define the checkpoint callback
checkpoint_callback = ModelCheckpoint(
    filepath='model_epoch_{epoch:03d}.keras',
    save_freq=save_freq,  # Integer number of batches between saves
    save_weights_only=False,  # Save the entire model
    verbose=1
)

# Add the callbacks
callbacks = [ModelMonitor(), checkpoint_callback]

"""# 4.4 train"""

hist = fashgan.fit(ds, epochs=2000, callbacks=[ModelMonitor()])

"""# 4.5 review performance"""

#plt.subtitle('Loss')
plt.plot(hist.history['d_loss'],label='d_loss')
plt.plot(hist.history['g_loss'],label='g_loss')
plt.legend()
plt.show()

"""# 5 test out Generator

# 5.1 Generate images
"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.models import model_from_json
import h5py

# Load the model architecture from the H5 file
with h5py.File('generatormodel.h5', 'r') as f:
    model_config = f.attrs.get('model_config')

# Convert bytes to string if necessary (depending on your Python version)
if isinstance(model_config, bytes):
    model_config = model_config.decode()

# Remove the 'groups' argument from the model configuration
model_config = model_config.replace('"groups": 1,', '')

# Recreate the model from the modified config
model = model_from_json(model_config, custom_objects={"Sequential": Sequential})

# Load weights into the model
with h5py.File('generatormodel.h5', 'r') as f:
    model.load_weights(f)

# Print the summary to check the model
model.summary()

from tensorflow.keras.models import load_model

# Load the model
model = load_model('generatormodel.h5')

# Print the model summary to inspect the layers
model.summary()

generator.load_weights(os.path.join('generatormodel.h5'))

imgs =generator.predict(tf.random.normal((16,128,1)))

fig,ax = plt.subplots(ncols=4,nrows=4,figsize=(20,20))
for r in range(4):
    for c in range(4):
        ax[r][c].imshow(imgs[(r+1)*(c+1)-1])

#saving the model
generator.save('generator.h5')
discriminator.save('discriminator.h5')