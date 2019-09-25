import argparse
import numpy
import math
import sys
from Queue import *
from PIL import Image

#take in command args
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--infile', type=str, help='path to vessel image (.bmp)')
parser.add_argument('-s', '--secretfile', type=str, help='path to image to be hidden (.bmp)')
opts = parser.parse_args()

#complexity funtion counts the number of changes of bits vertically + horizontaly
def complexity(matrix):
    #max is equivialant to the complexity of a checkerboard
    maxim = ((matrix.shape[0]-1)*matrix.shape[1]) + ((matrix.shape[1] - 1) * matrix.shape[0])
    curr = 0.0
    first = matrix[0,0]
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if (first != matrix[i,j]):
                curr = curr + 1
                first = matrix[i,j]
    
    first = matrix[0,0]
    for i in range(matrix.shape[1]):
        for j in range(matrix.shape[0]):
            if (first != matrix[j,i]):
                curr = curr + 1
                first = matrix[j,i]
    return curr/maxim


#Load Images and show images
print('Opening image files and showing vessel then secret...')
image = Image.open(opts.infile).convert('L')
secret = Image.open(opts.secretfile).convert('L')
image.show()
secret.show()

#Convert Images to Array
array = numpy.array(image)
secretArr = numpy.array(secret)

# Garbage collect files
image.close()
secret.close()

#Slice BitPlane of vessel
print('Slicing vessel...')
bitPlaneArr  = numpy.zeros( (array.shape[0], array.shape[1], 8), dtype = 'uint8' )
bitPlaneArr[:,:,0] = numpy.copy(array)
for i in range(bitPlaneArr.shape[0]):
    for j in range(bitPlaneArr.shape[1]):
        bitArr = numpy.unpackbits(numpy.uint8(bitPlaneArr[i,j,0]))
        for k in range(8):
            bitPlaneArr[i,j,k] =  bitArr[k]
del array
print('Sliced vessel.')

#Slice BitPlane of image to be hidden
print('Slicing secret image to be hidden...')
secretBitPlane = numpy.zeros( (secretArr.shape[0], secretArr.shape[1], 8), dtype = 'uint8' )
secretBitPlane[:,:,0] = numpy.copy(secretArr)
for i in range(secretBitPlane.shape[0]):
    for j in range(secretBitPlane.shape[1]):
        bitArr = numpy.unpackbits(numpy.uint8(secretBitPlane[i,j,0]))
        for k in range(8):
            secretBitPlane[i,j,k] =  bitArr[k]
del secretArr            
print('Sliced secret image.')


# chop up secret image into 8x8 bitplanes and place in a queue
print('Placing each 8x8 bit of secret into a queue...')
q = Queue(maxsize=0)
for k in range(7, -1, -1):
    for i in range(secretBitPlane.shape[0]/8):
        for j in range(secretBitPlane.shape[1]/8):
            q.put(secretBitPlane[slice(i*8, i*8+8),slice(j*8, j*8+8), k])
if(q.empty()):
    print('Queueing Failed: Secret image not large enough to embed')
    sys.exit(1)
print('Queue filled.')


#find places in bitPlaneArr to replace with 8x8s from queue
print('Placing each 8x8 element in queue into vessel bitplane...')
firstRun = True
#iterate through bitplane by 9x9s starting from the least signifigant layer
for k in range(7, -1, -1):
    for i in range(bitPlaneArr.shape[0]/9):
        for j in range(bitPlaneArr.shape[1]/9):

            #find a 8x8 that is static enough to be replaced
            if(not q.empty()):
                if(complexity(bitPlaneArr[slice(i*9, i*9+8),slice(j*9, j*9+8), k]) > .45):

                    #instead of storing the first secert 8x8 image in the first aplicable 9x9
                    #it is used to store metadata about the secret image, namely
                    # - the number of 8x8s in the queue, the number of height, and the number of width pixels
                    if(firstRun):
                        firstSquare = numpy.zeros( (9, 9), dtype = 'uint8')
                        
                        totalSquares = numpy.binary_repr(q.qsize(), width=27)
                        sizei = numpy.binary_repr(secretBitPlane.shape[0] - (secretBitPlane.shape[0]%8), width=18)
                        sizej = numpy.binary_repr(secretBitPlane.shape[1] - (secretBitPlane.shape[1]%8), width=18)

                        #first 27 bits holds the total number of 8x8s in the queue
                        charIndex = 0
                        for fSi in range(3):
                            for fSj in range(9):
                                if(totalSquares[charIndex] == '0'):
                                    firstSquare[fSi,fSj] = 0
                                elif(totalSquares[charIndex] == '1'):
                                    firstSquare[fSi,fSj] = 1
                                charIndex = charIndex+1
                        charIndex = 0
                        
                        #next 18 bits hold the height dimension
                        for fSi in range(2):
                            for fSj in range(9):
                                if(sizei[charIndex] == '0'):
                                    firstSquare[fSi+3,fSj] = 0
                                elif(sizei[charIndex] == '1'):
                                    firstSquare[fSi+3,fSj] = 1
                                charIndex = charIndex+1
                        charIndex = 0

                        #next 18 bits hold the width dimension
                        for fSi in range(2):
                            for fSj in range(9):
                                if(sizej[charIndex] == '0'):
                                    firstSquare[fSi+5,fSj] = 0
                                elif(sizej[charIndex] == '1'):
                                    firstSquare[fSi+5,fSj] = 1
                                charIndex = charIndex+1

                        #everything else is zeros

                        #Write first square into image
                        for fSi in range(9):
                            for fSj in range(9):
                                bitPlaneArr[i*9+fSi,j*9+fSj,k] = firstSquare[fSi,fSj]
                        firstRun = False

                    #write next queue element into bitplane array such the the 8x8 data square goes into
                    #the top left corner of the 9x9 bitplane area
                    else:   
                        dataSquare = numpy.copy(q.get())
                    
                        for dSi in range(dataSquare.shape[0]):
                            for dSj in range(dataSquare.shape[1]):
                                bitPlaneArr[i*9+dSi,j*9+dSj,k] = dataSquare[dSi,dSj]
                        #change the bitplanes last bit to 0 to signify that the area was not checkerboarded
                        bitPlaneArr[i*9+8, j*9+8, k] = 0

                    #at this point check to make sure that the replaced area is still suffiently noisy
                    #and if not, xor it with a checkerboard to ensure it is noisy enough to be picked out by
                    if(complexity(bitPlaneArr[slice(i*9, i*9+8),slice(j*9, j*9+8), k]) <= .45):
                        for cBi in range(9):
                            for cBj in range(9):
                                if((cBi + cBj)%2 == 0):
                                    if(bitPlaneArr[i*9+cBi,j*9+cBj,k] == 0):
                                        bitPlaneArr[i*9+cBi,j*9+cBj,k] = 1
                                    elif(bitPlaneArr[i*9+cBi,j*9+cBj,k] == 1):
                                        bitPlaneArr[i*9+cBi,j*9+cBj,k] = 0
                        #since we checkerboarded the area the last bit is changed to 1 to show that
                        bitPlaneArr[i*9+8, j*9+8, k] = 1

# confirm that all of vessel was able to be place
if(not q.empty()):
    print('Embedding failed: Vessel does not contain enough noisy sectors to fit all of secret image')
    sys.exit(1)
print('Noisy vessel bitplane replaced with secret image.')
del secretBitPlane
del q

#create an uint8 image from bitplane with embedded secret 
print('Creating image from embedded bitmap...')
intValue = numpy.uint8(0)
saveArr = numpy.copy(bitPlaneArr[:,:,0])
for i in range(saveArr.shape[0]):
    for j in range(saveArr.shape[1]):
        intValue = numpy.uint8(0)
        for k in range(8):
            intValue = numpy.uint8(intValue + (bitPlaneArr[i,j,k] * 2**(7-k)))
        saveArr[i,j] = intValue
del bitPlaneArr
print('New image created.')

#print bitPlaneArr with inbedded info and then save to file
print('Showing image and saving as "embedded.bmp"...')
newImage = Image.fromarray(saveArr,mode="L")
newImage.show()
newImage.save('embedded.bmp')
newImage.close()
print('Done.')