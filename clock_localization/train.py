from __future__ import division

import sys
sys.path.insert(0, '../')

from keras import backend as keras

from keras.preprocessing import sequence
from dateutil import parser
import numpy as np
import coremltools
import model
import data
import json
import operator
import keras.callbacks
import random
import time
import sys
import math

import signal
import time
import coremltools

from PIL import Image,ImageDraw

######
# allows us to used ctrl-c to end gracefully instead of just dying
######
class SignalHandler:
  stop_processing = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.stop_processing = True
######

def Learn():
		
	# 1. create the model
	print("creating the model")
	_model = model.createModel(True)

	# 2. train the model
	print("initializing the generator")
	batch_size = 1
	generator = data.ClockGenerator(model.IMG_SIZE,model.INCLUDE_SECONDS_HAND,0.5)
	generator.shakeVariance = 0
	
	iterations = 1000000
		
	print("beginning training")
	handler = SignalHandler()
	i = 0
	while True:
		
		if handler.stop_processing:
			break
		
		#n = int(random.random() * 43200)
		n = 10000
		print(i)
		Train(generator,_model,n)
		i += n
		
		if i >= iterations:
			break
				
	
	_model.save(model.MODEL_H5_NAME)
	

def Convert():
	coreml_model = coremltools.converters.keras.convert(model.MODEL_H5_NAME,input_names='image',image_input_names='image', image_scale=1/255.0)
	coreml_model.author = 'Rocco Bowling'   
	coreml_model.short_description = 'is the image good clock face to send to the time detector'
	coreml_model.input_description['image'] = 'image of the clock face'
	coreml_model.save(model.MODEL_COREML_NAME)


def Train(generator,_model,n):
	
	train,label = generator.generateClocksForLocalization(model.MODEL_SUBDIVIDE,n)
	
	batch_size = 32
	if n < batch_size:
		batch_size = n
	
	_model.fit(train,label,batch_size=batch_size,shuffle=True,epochs=1,verbose=1)

def Test():
	_model = model.createModel(True)
	
	np.set_printoptions(threshold=20)
	
	generator = data.ClockGenerator(model.IMG_SIZE,model.INCLUDE_SECONDS_HAND,0.5)
	generator.shakeVariance = 0
	
	input,output = generator.generateClocksForLocalization(model.MODEL_SUBDIVIDE,20)
	
	results = _model.predict(input)
	
	
	correct = 0
	for i in range(0,len(output)):
		# save the image with the expect and predicted rectangles drawn on it??
		sourceImg = Image.fromarray(input[i].reshape(model.IMG_SIZE[1],model.IMG_SIZE[0]) * 255.0).convert("RGB")
				
		draw = ImageDraw.Draw(sourceImg)
		draw.rectangle(generator.GetCoordsFromOutput(output[i],model.IMG_SIZE), outline="green")
		draw.rectangle(generator.GetCoordsFromOutput(results[i],model.IMG_SIZE), outline="red")
		
		filepath = '/tmp/clock_%s_%d.png' % (generator.convertOutputToRect(output[i]), i)
		sourceImg.save(filepath)
		
	

if __name__ == '__main__':
	if sys.argv >= 2:
		if sys.argv[1] == "test":
			Test()
		elif sys.argv[1] == "learn":
			Learn()
		elif sys.argv[1] == "convert":
			Convert()
		else:
			Test2(sys.argv[2])
	else:
		Test()
	