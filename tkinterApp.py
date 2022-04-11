#####
# By: Maciej Walczak  
# This is a simple python tkinter app used to aid in highlighting the difference 
# between a chosen baseline and chosen slices
#
#####
# importing required packages
import tkinter
from tkinter import filedialog
from PIL import ImageTk, Image
from functools import partial
import numpy as np

# list of file formats that are accepted by this program
# more may work without much implementation but these are the ones that have been tested
ACCEPTED_FILE_FORMATS = ["tiff", "tif", "png", "ppm", "jpeg"]

rawImages = [] # list of images in their raw form used for scaling and calculations based off them 
resultPNG = [] # the resulting image generated 

# the currTK variables are the images that are currently on display using tkinter that must be in
# accessible to be viewed by tkinter
currTKImage = []
currTKResult = []

# used to fix race condition of the scale image function
def ReloadImages():
    if currTKImage != []:
        imageDisplay.config(image= currTKImage)
    if currTKResult != []:
        imageFinal.config(image=currTKResult)
    root.after(10, ReloadImages)

# changes the image being presented to the one on the slider
def SetImage(val):
    im = Image.fromarray(rawImages[int(val) - 1])
    global currTKImage
    im = im.resize((int(im.width * currImageScale.get()), int(im.height * currImageScale.get())))
    currTKImage = ImageTk.PhotoImage(im)
    imageDisplay.config(image= currTKImage)

# Wrapper to allow Slider to call same function
def ScaleSizeSlider(val):
    ScaleSize()

# scales the size of the images and location based off the image size value
def ScaleSize():
    # if no raw images exist dont do anything
    if rawImages == []:
        return 
    
    im = Image.fromarray(rawImages[int(currImageIndex.get()) - 1])
    global currTKImage
    im = im.resize((int(im.width * currImageScale.get()), int(im.height * currImageScale.get())))
    currTKImage = ImageTk.PhotoImage(im)
    imageDisplay.config(image= currTKImage)
    
    # if the result image is not rendered do not scale it
    if resultPNG == []:
        return

    resultIM = resultPNG
    global currTKResult
    resultIM = resultIM.resize((int(resultIM.width * currImageScale.get()), int(resultIM.height * currImageScale.get())))
    currTKResult = ImageTk.PhotoImage(resultIM)
    imageFinal.config(image=currTKResult)

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
    if int(fromImgNum.get()) < 1 or int(fromImgNum.get()) > len(rawImages):
        Alert("\"From\" value must be greater than 0 and less than the number of images")
        return False
    if int(toImgNum.get()) < 1 or int(toImgNum.get()) > len(rawImages):
        Alert("\"To\" value must be greater than 0 and less than the number of images")
        return False
    if int(toImgNum.get()) < int(fromImgNum.get()):
        Alert("\"To\" value must be greater than or equal to the \"From\" value")
        return False

    return True

# helper function used to blend two colors by a factor and returns a color
# Takes a factor and two rgb values a input returning the blended color
def BlendRGB(factor, color1 = [0,0,0], color2 = [255, 255, 255]):
    
    c1 = np.array(color1)
    c2 = np.array(color2)
    
    result = c1 * factor + c2 * (1 - factor)
    return result.astype(np.uint8)
    red = 0
    green = 0
    blue = 0
    if color1[0] > color2[0]:
        red = color2[0] + (factor * (color1[0] - color2[0]))
    else:
        red = color1[0] + (factor * (color2[0] - color1[0]))
        
    if color1[1] > color2[1]:
        green = color2[1] + (factor * (color1[1] - color2[1]))
    else:
        green = color1[1] + (factor * (color2[1] - color1[1]))
        
    if color1[2] > color2[2]:
        blue = color2[2] + (factor * (color1[2] - color2[2]))
    else:
        blue = color1[2] + (factor * (color2[2] - color1[2]))

    red = int(red)
    green = int(green)
    blue = int(blue)

    return np.array([red, green, blue], dtype=np.uint8)

# calculates the difference and highlights the pixels that match the specifications
def CalculateDiff():
    global currImageScale
    if not ValidateInput():
        return

    # calculates the baseline
    baseLine = rawImages[0] / currBase.get()
    for i in range(1, currBase.get()):
        baseLine = baseLine + (rawImages[i] / currBase.get())
    baseLine = baseLine.astype(int)
    baseLine = baseLine.astype(np.uint8)
    totalNum.set(str(np.count_nonzero(baseLine != 0)))

    # populates diffMaps with 2d arrays of the difference between the baseline and current image
    # negative values are set to 0 difference
    
    diffMaps = []
    for i in range(int(fromImgNum.get()) - 1, int(toImgNum.get())):
        curr = baseLine.astype(np.int16) - rawImages[i]
        curr = curr.clip(min = 0)
        diffMaps.append(curr.astype(np.uint8))

    # only shows the difference that is sufficient
    for i in range(len(diffMaps)):
        for iy, ix in np.ndindex(diffMaps[i].shape):
            if(diffMaps[i][iy][ix] < currDiff.get()):
                diffMaps[i][iy][ix] = 0
            else:
                diffMaps[i][iy][ix] = 255


    # Gets the resulting image that displays where the conditions are true
    resultMap = diffMaps[0]
    for i in range(1, len(diffMaps)):
        for iy, ix in np.ndindex(diffMaps[i].shape):
            if(resultMap[iy][ix] == 255 and diffMaps[i][iy][ix] == 255):
                resultMap[iy][ix] = 255
            else:
                resultMap[iy][ix] = 0

    resultNum.set(str(np.count_nonzero(resultMap == 255)))

    for iy, ix in np.ndindex(resultMap.shape):
        for i in range(int(fromImgNum.get()) - 1, int(toImgNum.get())):
            if resultMap[iy][ix] != 0:
                resultMap[iy][ix] = min(resultMap[iy][ix], rawImages[i][iy][ix])
    
    # draws the resulting image 
    im = Image.fromarray(resultMap).convert('RGB')
    resultRGB = np.array(im)
    for iy, ix, iz in np.ndindex(resultRGB.shape):
        if resultMap[iy][ix] != 0:
            factor = resultMap[iy][ix] / baseLine[iy][ix]
            resultRGB[iy][ix] = BlendRGB(factor,color1=[0,0,0], color2=[255,0,0])
    

    im = Image.fromarray(resultRGB)
    global resultPNG
    resultPNG = im
    #im = im.resize((int(im.width * currImageScale.get()), int(im.height * currImageScale.get())))

    ScaleSize()

# used as a helper function resetting the UI and 
def ResetInputsGui():
    # Updates the current image scale and display
    scaleCurrImg.config(to=len(rawImages))
    ScaleSize()

    # Updates the Base scale
    scaleBase.config(to=len(rawImages))
    
# Gets the files selected by the user and generates the image list and raw image list from the files
# this also runs the acrivator function allowing the user to 
def BrowseFiles():
    global rawImages
    global currImageScale
    chosenImagePaths = []
    chosenImagePaths = tkinter.filedialog.askopenfilenames(title = "Select Files")
    
    # if no files are chosen does not do any changes
    if len(chosenImagePaths) == 0:
        return
    loadedNum.set(len(chosenImagePaths))

    # makes sure all files are in the correct file format
    for im in chosenImagePaths:
        if (im.split('.', 1)[1]).lower() not in ACCEPTED_FILE_FORMATS:
            Alert("\"." + im.split('.', 1)[1] + "\" is not a supported file format")
            return

    rawImages.clear()
    # Generates Image list and raw image list in a sorta sloppy way
    for im in chosenImagePaths:
        fileType = im.split('.', 1)[1]
        
        # if the file is tiff check if it is a multiframe file and inset each frame as an image
        if fileType == "tiff" or fileType == "tif":
            tiffStack = Image.open(im)
            #print(tiffStack.info)
            if tiffStack.info.get("compression") != "raw":
                Alert("Warning the tiff file compression is not raw this may crash the app")
            for i in range (tiffStack.n_frames):
                tiffStack.seek(i)
                curr = tiffStack
                rawImages.append(np.array(curr))
                curr = curr.resize((int(curr.width * currImageScale.get()), int(curr.height * currImageScale.get())))

        else:
            curr = Image.open(im)
            rawImages.append(np.array(curr))
            curr = curr.resize((int(curr.width * currImageScale.get()), int(curr.height * currImageScale.get())))
    
    ResetInputsGui()

# saves the generated image to the filename specified
def SaveToFile():
    if resultPNG == []:
        Alert("No Image has been generated")
        return
    
    file = tkinter.filedialog.asksaveasfile(
        initialfile="result.png", 
        defaultextension=".png",
    )
    if file is not None:
        resultPNG.save(file.name, "PNG")

if __name__ == "__main__":
    # creating main window
    root = tkinter.Tk()
    root.geometry('900x400')
    root.title("Tkinter App")

    # coordinates for where the top left corner of the image viewing modules will generate
    ciX = 230
    ciY = 60



    # The Module that holds the sliders and input for the variables GUI
    lfAnnalysis = tkinter.LabelFrame(root, text="Process Variables")
    lfAnnalysis.grid(row=0,column=0, padx=(10, 0), sticky="n")

    # Draws Base scale and label
    baseLabel = tkinter.Label(lfAnnalysis, text="Base Count:")
    baseLabel.grid(row=0,column=0, pady=(15,0))
    currBase = tkinter.IntVar()
    currBase.set(1)
    scaleBase = tkinter.Scale(lfAnnalysis, variable=currBase, from_=1, to=1, orient = tkinter.HORIZONTAL)
    scaleBase.grid(row=0,column=1)
    
    # Draws Difference scale and label
    diffLabel = tkinter.Label(lfAnnalysis, text="Difference amount:")
    diffLabel.grid(row=1,column=0, pady=(15,0))
    currDiff = tkinter.IntVar()
    currDiff.set(40)
    scaleDiff = tkinter.Scale(lfAnnalysis, variable=currDiff, from_=0, to=100, orient= tkinter.HORIZONTAL)
    scaleDiff.grid(row=1,column=1)

    # Sub module used to select which images to check
    lfCheck = tkinter.LabelFrame(lfAnnalysis, text = "Check Images")
    lfCheck.grid(row=2, column=0, columnspan=2)

    # Draws Check Images UI
    labelCheckFrom = tkinter.Label(lfCheck, text="From:")
    labelCheckFrom.grid(row=0, column=0)
    labelCheckTo = tkinter.Label(lfCheck, text="To:")
    labelCheckTo.grid(row=0, column=2)
    fromImgNum = tkinter.StringVar()
    inputFrom = tkinter.Entry(lfCheck, textvariable=fromImgNum, width=5)
    inputFrom.grid(row=0, column=1)
    toImgNum = tkinter.StringVar()
    inputFrom = tkinter.Entry(lfCheck, textvariable=toImgNum, width=5)
    inputFrom.grid(row=0, column=3, padx=(0, 10), pady=(10,10))

    # Draws buttons
    calculateButton = tkinter.Button(lfAnnalysis, text="Calculate", command=CalculateDiff)
    calculateButton.grid(row=3, column=1, pady=(10, 10), padx = (10, 0))



    # Module that contains ability to load files holds information about them
    lfImageInput = tkinter.LabelFrame(root, text="Import Files")
    lfImageInput.grid(row=0, column=1, sticky="nw")

    # Creates button to start file explorer for images needed to be analyzed
    buttonGetPNGs = tkinter.Button(lfImageInput, text="Find Images", command=BrowseFiles)
    buttonGetPNGs.grid(row=0, column=3, padx=(10,100), pady=(0,10))

    # Label informing the amount of images loaded
    labelImagesLoaded = tkinter.Label(lfImageInput, text="Images Loaded:")
    labelImagesLoaded.grid(row=0, column=0)
    loadedNum = tkinter.StringVar()
    loadedNum.set("NaN")
    labelImagesNum = tkinter.Entry(lfImageInput, textvariable=loadedNum, width=5, state='readonly')
    labelImagesNum.grid(row=0, column=1)



    # Module that contains ability to save results and holds information about result image
    lfSave= tkinter.LabelFrame(root, text="Result")
    lfSave.grid(row=0, column=2, sticky="n")

    # Draws number of pixels that fulfull the requirement
    labelResultingNumTitle = tkinter.Label(lfSave, text="Number of Pixels:")
    labelResultingNumTitle.grid(row=0, column=0)
    resultNum = tkinter.StringVar()
    resultNum.set("NaN")
    labelResultingNum = tkinter.Entry(lfSave, textvariable=resultNum,width=5 ,state='readonly')
    labelResultingNum.grid(row=0,column=1)

    # Draws total number of pixels in image
    labelTotalNumTitle = tkinter.Label(lfSave, text="Total Pixels:")
    labelTotalNumTitle.grid(row=0, column=2)
    totalNum = tkinter.StringVar()
    totalNum.set("NaN")
    labelTotalNum = tkinter.Entry(lfSave, textvariable=totalNum,width=5 ,state='readonly')
    labelTotalNum.grid(row=0, column=3)

    saveButton = tkinter.Button(lfSave, text="Save to file", command=SaveToFile)
    saveButton.grid(row=0, column=4, pady=(0,10), padx=(10,10))




    # Draws current image scale and its label
    labelCurrImg = tkinter.Label(root, text="Current Image:")
    labelCurrImg.place(x=ciX+0, y=ciY+20)
    currImageIndex = tkinter.IntVar()
    scaleCurrImg = tkinter.Scale(root, from_=1, to=1, variable=currImageIndex, orient = tkinter.HORIZONTAL, command=SetImage)
    scaleCurrImg.place(x=ciX+90, y=ciY+0)
    
    # Draws size scale and its label
    currImageScale = tkinter.DoubleVar()
    currImageScale.set(1.0)
    scaleImage = tkinter.Scale(root, variable=currImageScale, from_=0.1, to=5, orient=tkinter.VERTICAL, resolution=0.05, command=ScaleSizeSlider)
    scaleImage.place(x=ciX+30, y=ciY+50)
    labelImageScale = tkinter.Label(root, text="Scale:")
    labelImageScale.place(x=ciX+0, y=ciY+90)

    # Module managing location of loaded and result images
    lfImages = tkinter.Label(root)
    lfImages.place(x=ciX+80, y=ciY+40)
    
    # Draws the orginial image set 
    imageDisplay = tkinter.Label(lfImages)
    imageDisplay.pack(side="left")
    # Draws the result image initial is copy of first from image set
    imageFinal = tkinter.Label(lfImages)
    imageFinal.pack(side="left")



    # running the application and the function being executed in parallel
    root.after(100, ReloadImages)
    root.mainloop()