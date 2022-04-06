#####
# By: Maciej Walczak  
# This is a simple python tkinter app used to highlight the
#
#
#####
# importing required packages
from glob import glob
import tkinter
from tkinter import filedialog
from unittest import result
from PIL import ImageTk, Image
import os
from functools import partial
from matplotlib.pyplot import show
import numpy as np
from sklearn.preprocessing import scale

chosenImagePaths = []

currImageScale = 2
rawImages = []
baseLine = []
resultImage = []
diffMaps = []
resultMap = []

imageList = []

# changes the image being presented to the one on the slider
def SetImage(target, val):
    target.config(image = imageList[int(val)])

# calculates the difference and highlights the pixels that match the specifications
def CalculateDiff(target):
    # calculates the baseline
    global baseLine
    baseLine = rawImages[0] / currBase.get()
    for i in range(1, currBase.get()):
        baseLine = baseLine + (rawImages[i] / currBase.get())
    baseLine = baseLine.astype(int)
    baseLine = baseLine.astype(np.uint8)

    # populates diffMaps with 2d arrays of the difference between the baseline and current image
    # negative values are set to 0 difference
    global diffMaps
    diffMaps.clear()
    for i in range(currBase.get(), len(rawImages)):
        curr = baseLine.astype(np.int16) - rawImages[i]
        curr = curr.clip(min = 0)
        diffMaps.append(curr.astype(np.uint8))


    # only shows the difference that is sufficient
    for i in range(len(diffMaps) - 1):
        for iy, ix in np.ndindex(diffMaps[i].shape):
            if(diffMaps[i][iy][ix] < currDiff.get()):# and diffMaps[i + 1][iy][ix] < currDiff.get()):
                diffMaps[i][iy][ix] = 0
            else:
                diffMaps[i][iy][ix] = 255


    # Gets the resulting image that displays where the conditions are true
    global resultMap
    resultMap = diffMaps[0]
    for i in range(1, len(diffMaps)):
        resultMap = resultMap + diffMaps[i]

    # draws the resulting image 
    im = Image.fromarray(resultMap)
    im = im.resize((int(im.width * currImageScale), int(im.height * currImageScale)))
    global resultImage 
    resultImage = ImageTk.PhotoImage(im)

    target.config(image = resultImage)

def BrowseFiles():
    global chosenImagePaths
    chosenImagePaths = tkinter.filedialog.askopenfiles(title = "Select Files")
    print(chosenImagePaths)

# saves the generated image to the filename specified
def SaveToFile():
    print("Not inplemented yet!")

if __name__ == "__main__":

    # hard coded paths used for debugging
    imagePaths = []
    for i in range(15):
        if i < 10:
            imagePaths.append('For quantification png/acute intervention - 20220404_164345_pw040422_BBBO_2_acute_intervention_1_1 - seq no  8 -1000'+str(i)+'.png')
        else:
            imagePaths.append('For quantification png/acute intervention - 20220404_164345_pw040422_BBBO_2_acute_intervention_1_1 - seq no  8 -100'+str(i)+'.png')
    

    # creating main window
    root = tkinter.Tk()
    root.geometry('700x400')
    root.title("App")

    # Creates button to start file explorer for images needed to be analyzed
    buttonGetPNGs = tkinter.Button(root, text="Find Images", command=BrowseFiles)
    buttonGetPNGs.place(x= 300, y = 30)

    # creates an image list from the selection
    # and a list of values to be edited
    for path in imagePaths:
        currImage = Image.open(path)
        rawImages.append(np.array(currImage))
        currImage = currImage.resize((int(currImage.width * currImageScale), int(currImage.height * currImageScale)))
        imageList.append(ImageTk.PhotoImage(currImage))
    

    # Draws the orginial image set 
    imageDisplay = tkinter.Label(root, image = imageList[0])
    imageDisplay.place(x=300, y=100)

    labelCurrImg = tkinter.Label(root, text="Current Image:")
    labelCurrImg.place(x= 290, y=80)
    scaleCurrImg = tkinter.Scale(root, from_=0, to=14, orient = tkinter.HORIZONTAL, command=partial(SetImage, imageDisplay))
    scaleCurrImg.place(x = 380, y=60)

    # Draws the result image initial is copy of first from image set
    imageFinal = tkinter.Label(root, image = imageList[0])
    imageFinal.place(x = 500, y = 100)

    # Draws Base scale and label
    baseLabel = tkinter.Label(root, text="Base Count:")
    baseLabel.place(x=5, y=20)
    currBase = tkinter.IntVar()
    currBase.set(3)
    scaleBase = tkinter.Scale(root, variable=currBase, from_=1, to=5, orient = tkinter.HORIZONTAL)
    scaleBase.place(x=120, y =0)
    
    # Draws Difference scale and label
    diffLabel = tkinter.Label(root, text="Difference amount:")
    diffLabel.place(x=5, y=60)
    currDiff = tkinter.IntVar()
    currDiff.set(40)
    scaleDiff = tkinter.Scale(root, variable=currDiff, from_=0, to=100, orient= tkinter.HORIZONTAL)
    scaleDiff.place(x=120, y=40)


    # Draws Required Ajacent scale and label    
    reqAdjLabel = tkinter.Label(root, text="Required Adjacent:")
    reqAdjLabel.place(x=5, y=100)
    reqAdj = tkinter.IntVar()
    reqAdj.set(2)
    reqAdjScale = tkinter.Scale(root, variable=reqAdj, from_=1, to= 4, orient= tkinter.HORIZONTAL)
    reqAdjScale.place(x=120, y=80)

    # Draws buttons
    calculateButton = tkinter.Button(root, text="Calculate", command=partial(CalculateDiff, imageFinal))
    calculateButton.place(x=10,y=200)
    saveButton = tkinter.Button(root, text="Save to file", command=SaveToFile)
    saveButton.place(x=500, y=350)
    

    currImage = imageDisplay

    

    # running the application
    root.mainloop()