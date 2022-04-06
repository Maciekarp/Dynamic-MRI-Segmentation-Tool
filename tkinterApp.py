#####
# By: Maciej Walczak  
# This is a simple python tkinter app used to highlight the
#
#
#####
# importing required packages
#from curses import raw
#from glob import glob
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
    target.config(image = imageList[int(val) - 1])

# used to show a message to the user in a new window
def Alert(message):
    alertBox = getattr(tkinter.messagebox, 'show{}'.format('info'))
    alertBox("Alert", message)

# used to validate the numbers user inputed in the UI
# returns true if all values are acceptable
def ValidateInput():
    if not fromImgNum.get().isdigit():
        Alert("\"From\" value must be a number")
        return False
    if not toImgNum.get().isdigit():
        Alert("\"To\" value must be a number")
        return False
    if int(fromImgNum.get()) < 1 or int(fromImgNum.get()) > len(imageList):
        Alert("\"From\" value must be greater than 0 and less than the number of images")
        return False
    if int(toImgNum.get()) < 1 or int(toImgNum.get()) > len(imageList):
        Alert("\"To\" value must be greater than 0 and less than the number of images")
        return False
    if int(toImgNum.get()) < int(fromImgNum.get()):
        Alert("\"To\" value must be greater than or equal to the \"From\" value")
        return False

    return True

# calculates the difference and highlights the pixels that match the specifications
def CalculateDiff(target):
    if not ValidateInput():
        return

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
    for i in range(int(fromImgNum.get()) - 1, int(toImgNum.get())):
        curr = baseLine.astype(np.int16) - rawImages[i]
        curr = curr.clip(min = 0)
        diffMaps.append(curr.astype(np.uint8))
    
    #for i in range(currBase.get(), len(rawImages)):
    #    curr = baseLine.astype(np.int16) - rawImages[i]
    #    curr = curr.clip(min = 0)
    #    diffMaps.append(curr.astype(np.uint8))


    # only shows the difference that is sufficient
    for i in range(len(diffMaps)):
        for iy, ix in np.ndindex(diffMaps[i].shape):
            if(diffMaps[i][iy][ix] < currDiff.get()):
                diffMaps[i][iy][ix] = 0
            else:
                diffMaps[i][iy][ix] = 255


    # Gets the resulting image that displays where the conditions are true
    global resultMap
    resultMap = diffMaps[0]
    for i in range(1, len(diffMaps)):
        for iy, ix in np.ndindex(diffMaps[i].shape):
            if(resultMap[iy][ix] == 255 and diffMaps[i][iy][ix] == 255):
                resultMap[iy][ix] = 255
            else:
                resultMap[iy][ix] = 0

        #resultMap = resultMap + diffMaps[i]
    resultNum.set(str(np.count_nonzero(resultMap == 255)))


    # draws the resulting image 
    im = Image.fromarray(resultMap)
    im = im.resize((int(im.width * currImageScale), int(im.height * currImageScale)))
    global resultImage 
    resultImage = ImageTk.PhotoImage(im)

    target.config(image = resultImage)


# used as a helper function resetting the UI and 
def ResetInputsGui():
    #global scaleCurrImg

    scaleCurrImg.config(to=len(imageList))
    #currBase.set(min(currBase.get(), len(imageList)))
    imageDisplay.config(image=imageList[0])
    pass

# Gets the files selected by the user and generates the image list and raw image list from the files
# this also runs the acrivator function allowing the user to 
def BrowseFiles():
    global chosenImagePaths
    global rawImages
    global imageList
    chosenImagePaths = tkinter.filedialog.askopenfiles(title = "Select Files")
    imageList.clear()
    rawImages.clear()
    # Generates Image list and raw image list in a sorta sloppy way
    for im in chosenImagePaths:
        #print(im.name)
        curr = Image.open(im.name)
        rawImages.append(np.array(curr))
        curr = curr.resize((int(curr.width * currImageScale), int(curr.height * currImageScale)))
        imageList.append(ImageTk.PhotoImage(curr))
    ResetInputsGui()


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
    scaleCurrImg = tkinter.Scale(root, from_=1, to=15, orient = tkinter.HORIZONTAL, command=partial(SetImage, imageDisplay))
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


    # Draws Check Images UI
    labelCheckTitle = tkinter.Label(root, text="Check Images:")
    labelCheckTitle.place(x=5, y=100)
    labelCheckFrom = tkinter.Label(root, text="From:")
    labelCheckFrom.place(x=40, y=120)
    labelCheckTo = tkinter.Label(root, text="To:")
    labelCheckTo.place(x=120, y=120)
    fromImgNum = tkinter.StringVar()
    inputFrom = tkinter.Entry(root, textvariable=fromImgNum, width=5)
    inputFrom.place(x=80 ,y=120)
    toImgNum = tkinter.StringVar()
    inputFrom = tkinter.Entry(root, textvariable=toImgNum, width=5)
    inputFrom.place(x=140 ,y=120)

    # Draws number of pixels that are 
    labelResultingNumTitle = tkinter.Label(root, text="Number of Pixels:")
    labelResultingNumTitle.place(x=500, y=320)
    resultNum = tkinter.StringVar()
    resultNum.set("NaN")
    labelResultingNum = tkinter.Entry(root, textvariable=resultNum,width=5 ,state= tkinter.DISABLED)
    labelResultingNum.place(x=610, y=320)

    # Draws buttons
    calculateButton = tkinter.Button(root, text="Calculate", command=partial(CalculateDiff, imageFinal))
    calculateButton.place(x=10,y=200)
    saveButton = tkinter.Button(root, text="Save to file", command=SaveToFile)
    saveButton.place(x=500, y=350)
    
    currImage = imageDisplay

    

    # running the application
    root.mainloop()