import argparse
import numpy
import math
from Queue import *
from PIL import Image

#take in command args
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--infile', type=str, help='path to image embedded with secret (.bmp)')
opts = parser.parse_args()

#complexity funtions count the number of changes of bits vertically + horizontaly
def complexity(matrix):
    #max is equivialant to the complexity of a checkerboard
    max = ((matrix.shape[0]-1)*matrix.shape[1]) + ((matrix.shape[1] - 1) * matrix.shape[0])
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
    return curr/max


#Load Images and show image
print('Opening embedded image and showing...')
image = Image.open(opts.infile).convert('L')
image.show()

#Convert Image to Array
array = numpy.array(image)

# Garbage collect file
image.close()

#Slice BitPlane of vessel
print('Slicing image...')
bitPlaneArr  = numpy.zeros( (array.shape[0], array.shape[1], 8), dtype = 'uint8' )
bitPlaneArr[:,:,0] = numpy.copy(array)
for i in range(bitPlaneArr.shape[0]):
    for j in range(bitPlaneArr.shape[1]):
        bitArr = numpy.unpackbits(numpy.uint8(bitPlaneArr[i,j,0]))
        for k in range(8):
            bitPlaneArr[i,j,k] =  bitArr[k]
del array
print('Sliced vessel.')


# chop up embedded image into noisy 8x8 with 1x1 padding bitplanes and place in a queue for decoding
print('Placing each noisy 9x9 bit of vessel into a queue...')
q = Queue(maxsize=0)
for k in range(7, -1, -1):
    for i in range(bitPlaneArr.shape[0]/9):
        for j in range(bitPlaneArr.shape[1]/9):
            if(complexity(bitPlaneArr[slice(i*9, i*9+8),slice(j*9, j*9+8), k]) > .45):
                q.put(bitPlaneArr[slice(i*9, i*9+9),slice(j*9, j*9+9), k])
print('Queue filled.')

#first hidden square contains metadata and is not part of the image
print('Checking metadata in first 9x9 and creating empty bitplane for embedded secret...')
firstSquare = q.get()
#check if first square was checkerboarded and if so un-checkerboard
if(firstSquare[8,8] == 1):
    for i in range(9):
        for j in range(9):
            if((i + j)%2 == 0):
                if(firstSquare[i,j] == 0):
                    firstSquare[i,j] = 1
                elif(firstSquare[i,j] == 1):
                    firstSquare[i,j] = 0
    firstSquare[8,8] == 0

#bit count first 27 bit uint as # of 8x8 squares in image (how many elements needed from queue)
totalSquares = 0
bitValue = 26
for i in range(3):
        for j in range(9):
            if(firstSquare[i,j] == 1):
                totalSquares = totalSquares + (2**bitValue)
            bitValue = bitValue-1

#bit count 18 bit uint as height dimension
sizei = 0
bitValue = 17
for i in range(2):
        for j in range(9):
            if(firstSquare[i+3,j] == 1):
                sizei = sizei + (2**bitValue)
            bitValue = bitValue-1

#bit count 18 bit uint as width dimension
sizej = 0
bitValue = 17
for i in range(2):
        for j in range(9):
            if(firstSquare[i+5,j] == 1):
                sizej = sizej + (2**bitValue)
            bitValue = bitValue-1

#create a bitplane to hold entire secret image using above dimensions
secretArr = numpy.zeros( (sizei, sizej, 8), dtype = 'uint8' )
print('Empty bitplane ready for data.')

    
#copy data to secret array
print('Decoding queue and placing in Secret bitplane...')
done = 0
#iterate through empty secretArr by 8x8s starting from the least signifigant layer
for k in range(7, -1, -1):
    for i in range((secretArr.shape[0])/8):
        for j in range((secretArr.shape[1])/8):

            # if there are still relevant data squares in the queue
            if(done < totalSquares):
                # get 9x9 data square
                dataSquare = numpy.copy(q.get())
                # use last bit to determine if images was checkerboarded and un-checkerboard if so
                if(dataSquare[8,8] == 1):
                    for dSi in range(9):
                        for dSj in range(9):
                            if((dSi + dSj)%2 == 0):
                                if(dataSquare[dSi,dSj] == 0):
                                    dataSquare[dSi,dSj] = 1
                                elif(dataSquare[dSi,dSj] == 1):
                                    dataSquare[dSi,dSj] = 0
                    dataSquare[8,8] == 0

                #copy 8x8 corner of dataSqaure into secretArr    
                secretArr[slice(i*8,i*8+8), slice(j*8,j*8+8), k] = dataSquare[slice(8), slice(8)]
                done = done + 1
print('Secret bitplane complete.')

#create an uint8 image from bitplane with embedded secret 
print('Creating image from decoded bitplane...')
intValue = numpy.uint8(0)
saveArr = numpy.copy(secretArr[:,:,0])
for i in range(saveArr.shape[0]):
    for j in range(saveArr.shape[1]):
        intValue = numpy.uint8(0)
        for k in range(8):
            intValue = numpy.uint8(intValue + (secretArr[i,j,k] * 2**(7-k)))
        saveArr[i,j] = intValue
del secretArr
print('Image of decoded data created.')

#print bitPlaneArr with inbedded info and then save to file
print('Showing decoded image and saving as "decoded.bmp"...')
newImage = Image.fromarray(saveArr,mode="L")
newImage.show()
newImage.save('decoded.bmp')
newImage.close()
print('Done.')