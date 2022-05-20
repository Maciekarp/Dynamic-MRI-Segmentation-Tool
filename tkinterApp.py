#####
# By: Maciej Walczak  
# This is a simple python tkinter app used to aid in highlighting the difference 
# between a chosen baseline and chosen slices
#
#####
# importing required packages
import tkinter
from tkinter import NW, filedialog, messagebox
from PIL import ImageTk, Image, ImageFile
from functools import partial
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import ttk
import pandas as pd

# list of file formats that are accepted by this program
# more may work without much implementation but these are the ones that have been tested
ACCEPTED_FILE_FORMATS = ["tiff", "tif", "png", "ppm", "jpeg"]

rawImages = [] # list of images in their raw form used for scaling and calculations based off them 
resultPNG = [] # the resulting image generated 
resultMap = [] # the resulting 2d value map of the image

dragged = False

# the currTK variables are the images that are currently on display using tkinter that must be in
# accessible to be viewed by tkinter
currTKImage = []
currTKResult = []

selectionBox = {"xStart": 0, "xEnd": 0, "yStart":0, "yEnd":0}

initialClickX = 0
initialClickY = 0

# this allows corrupted files to be used and
ImageFile.LOAD_TRUNCATED_IMAGES = True

shiftHeld = False
imageHover = False

# used 
finalXPos = 50

graphVals = []

# offset of the images from the corner of the canvas
X_OFFSET = 10
Y_OFFSET = 10

def loop():
    if imageHover and shiftHeld:
        SetFleur()
    else:
        SetArrow()
    root.after(5, loop)

def clamp(num, min_value, max_value):
        num = max(min(num, max_value), min_value)
        return num

def ImageEnter(event):
    global imageHover 
    imageHover = True

def ImageExit(event):
    global imageHover 
    imageHover = False

def ShiftDown(event):
    global shiftHeld
    shiftHeld = True
    
def ShiftUp(event):
    global shiftHeld
    shiftHeld = False
    
def SetFleur():
    root.config(cursor="fleur")

def SetArrow():
    root.config(cursor="arrow")

# helper function used for conversion from position on canvas to pixel coordinate in rawImages array
def ToCoord(x, y):
    return int((x - X_OFFSET) / currImageScale.get()), int((y - Y_OFFSET) / currImageScale.get())

# Helper function used for conversion from pixel coordinate in rawImages array to position on canvas
def ToImagePos(x, y):
    return int(x * currImageScale.get() + X_OFFSET), int(y * currImageScale.get() + Y_OFFSET)

# Refreshes the selection boxes to display correctly selected pixels
def SetBox():
    global selectionBox
    global selectionSquareDisplay
    global selectionSquareFinal
    x1, y1 = ToImagePos(selectionBox["xStart"], selectionBox["yStart"])
    x2, y2 = ToImagePos(selectionBox["xEnd"], selectionBox["yEnd"])

    canvasImages.delete(selectionSquareDisplay)
    selectionSquareDisplay = canvasImages.create_rectangle(
        x1, y1, x2, y2, outline="red")

    if resultPNG == []:
        return

    canvasImages.delete(selectionSquareFinal)
    selectionSquareFinal = canvasImages.create_rectangle(
        x1 + finalXPos, y1, x2 + finalXPos, y2, outline="red"
    )

# Event that occurs when image on canvas is clicked
def ClickOnImage(event):
    global selectionBox
    # if shift held move box around
    if shiftHeld:
        # if box does not exist do not do anything
        if selectionBox["xStart"] == 0 and selectionBox["yStart"] == 0 and selectionBox["xEnd"] == 0 and  selectionBox["yEnd"] == 0:
            return 
        global initialClickX
        global initialClickY
        initialClickX, initialClickY = ToCoord(event.x, event.y)
    else:
        
        x, y = ToCoord(event.x, event.y)
        selectionBox["xStart"] = x
        selectionBox["yStart"] = y

# Event that occurs when image on canvas is dragged
def DragOnImage(event):
    global dragged
    dragged = True
    global selectionBox

    x, y = ToCoord(event.x, event.y)
    
    selectionBox["xEnd"] = clamp(x, 0, len(rawImages[0][0]))
    selectionBox["yEnd"] = clamp(y, 0, len(rawImages[0]))
    SetBox()

# Event that occurs when image on canvas is released
def ReleasedOnImage(event):
    global dragged
    if not dragged:
        selectionBox["xStart"] = 0
        selectionBox["xEnd"] = 0
        selectionBox["yStart"] = 0
        selectionBox["yEnd"] = 0
        SetBox()
    else:
        dragged = False

# Wrapper for when clicking on the result image 
def ClickOnResult(event):
    event.x = event.x - finalXPos
    ClickOnImage(event)

# Wrapper for when dragging on the result image 
def DragOnResult(event):
    event.x = event.x - finalXPos
    DragOnImage(event)

# Wrapper for when released on the result image 
def ReleasedOnResult(event):
    event.x = event.x - finalXPos
    ReleasedOnImage(event)



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
    im = im.resize((int(im.width * currImageScale.get()), int(im.height * currImageScale.get())), resample=0)
    currTKImage = ImageTk.PhotoImage(im)
    canvasImages.itemconfig(imageDisplay, image=currTKImage)

    # if the result image is not rendered do not scale it
    if resultPNG == []:
        SetBox()
        return

    resultIM = resultPNG
    global currTKResult
    global finalXPos
    resultIM = resultIM.resize((int(resultIM.width * currImageScale.get()), int(resultIM.height * currImageScale.get())), resample=0)
    currTKResult = ImageTk.PhotoImage(resultIM)
    
    canvasImages.itemconfig(imageFinal, image=currTKResult)
    finalXPos = 20 + im.width
    canvasImages.moveto(imageFinal, finalXPos + X_OFFSET , Y_OFFSET)
    
    SetBox()

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


# calculates the difference and highlights the pixels that match the specifications
def CalculateDiff():
    global currImageScale
    global resultMap
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
    colorDisplayed = [255, 0, 0]
    if doGrayScale.get() == 1:
        colorDisplayed = [255, 255, 255]
    for iy, ix, iz in np.ndindex(resultRGB.shape):
        if resultMap[iy][ix] != 0:
            if doGradient.get() == 1:
                factor = resultMap[iy][ix] / baseLine[iy][ix]
                resultRGB[iy][ix] = BlendRGB(factor,color1=[0,0,0], color2=colorDisplayed)
            else:
                resultRGB[iy][ix] = np.array(colorDisplayed).astype(np.uint8)
    


    im = Image.fromarray(resultRGB)
    global resultPNG
    resultPNG = im

    ScaleSize()

# used as a helper function resetting the UI and 
def ResetInputsGui():
    # Updates the current image scale and display
    scaleCurrImg.config(to=len(rawImages))
    ScaleSize()

    # Updates the Base scale
    scaleBase.config(to=len(rawImages))

    # Updates check images max values
    inputAUCFrom.config(to=len(rawImages))
    inputAUCTo.config(to=len(rawImages))
    inputFrom.config(to=len(rawImages))
    inputTo.config(to=len(rawImages))
    
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
        if (im.split('.')[-1]).lower() not in ACCEPTED_FILE_FORMATS:
            Alert("\"." + im.split('.', 1)[1] + "\" is not a supported file format")
            return

    rawImages.clear()
    # Generates Image list and raw image list in a sorta sloppy way
    for im in chosenImagePaths:
        fileType = im.split('.', 1)[1]
        
        # if the file is tiff check if it is a multiframe file and inset each frame as an image
        if fileType == "tiff" or fileType == "tif":
            tiffStack = Image.open(im)
            if tiffStack.info.get("compression") != "raw":
                Alert("Warning the tiff file compression is not raw this may crash the app")
            for i in range (tiffStack.n_frames):
                tiffStack.seek(i)
                rawImages.append(np.array(tiffStack))

        else:
            rawImages.append(np.array(Image.open(im)))
    
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
        # if you do 
        if doAlpha.get() == 0:
            resultPNG.save(file.name, "PNG")
        else:
            RGB = np.array(resultPNG)
            h, w = RGB.shape[:2]
            # Add an alpha channel, fully opaque (255)
            RGBA = np.dstack((RGB, np.zeros((h,w),dtype=np.uint8)+255))
            # Make all pixels matched by mask into transparent ones
            RGBA[(RGBA[:, :, 0:3] == [0,0,0]).all(2)] = (0,0,0,0)
            # Convert Numnpy array back to PIL Image and save
            Image.fromarray(RGBA).save(file.name, "PNG")

# Constructs a matplotlib graph from the images loaded
def ConstructGraph():
    if len(rawImages) == 0:
        Alert("No Images Selected")
        return
    if len(resultMap) == 0 and useResult.get():
        Alert("Result Image Not Generated")
        return
    graphFigure = Figure(figsize = (3.5, 3), dpi= 100)

    # getting the baseline by getting the average pixel value
    
    # if using the ROI change the loop constraints
    xList = []
    yList = []
    if useROI.get():
        if selectionBox["xStart"] > selectionBox["xEnd"]:
            yList = range(selectionBox["xEnd"], selectionBox["xStart"])
        else:
            yList = range(selectionBox["xStart"], selectionBox["xEnd"])
        
        if selectionBox["yStart"] > selectionBox["yEnd"]:
            xList = range(selectionBox["yEnd"], selectionBox["yStart"])
        else:
            xList = range(selectionBox["yStart"], selectionBox["yEnd"])
        
    else:
        xList = range(len(rawImages[0]))
        yList = range(len(rawImages[0][0]))

    countBase = 0
    countCurve = 0
    curve = [0] * len(rawImages)
    pixelTotalVal = 0
    for ix in xList:
        for iy in yList:
            if (not useResult.get()) or resultMap[ix][iy] != 0:
                countCurve += 1
                for i in range(len(rawImages)):
                    curve[i] += rawImages[i][ix][iy]
                for i in range(currBase.get()):
                    countBase += 1
                    pixelTotalVal += rawImages[i][ix][iy]
    if countBase == 0 or countCurve == 0:
        Alert("No pixels possible to graph")
        return
    pixelTotalVal = pixelTotalVal / countBase
    curve[:] = [x / countCurve for x in curve]

    # adding the subplot
    plot1 = graphFigure.add_subplot(111)    

    # plotting the graph and setting it up
    plot1.axhline(y=pixelTotalVal, color="r")
    plot1.plot(list(range(1, 1 + len(rawImages))), curve)

    
    plot1.set_xlabel("Frame", fontsize=10)
    plot1.set_ylabel("Avg Pixel Value", fontsize=10)
    #plot1.set_xlim(1, 1 + len(rawImages))
    plot1.set_ylim(0, 255)
    plot1.set_xticks(np.arange(1, 1 + len(rawImages), 1))
    graphFigure.tight_layout()

    # creating the Tkinter canvas
    # containing the Matplotlib figure
    graphCanvas = FigureCanvasTkAgg(graphFigure, master = lfAUC) 
    graphCanvas.get_tk_widget().grid(row=4, column=0, columnspan=5, padx=10, sticky="nw")
    graphCanvas.draw()

    ###############    TOOLBAR    ###############
    toolbarFrame = tkinter.Frame(lfAUC)
    toolbarFrame.grid(row=5,column=0, columnspan=5, sticky= "w", padx=(5,5))
    toolbar = NavigationToolbar2Tk(graphCanvas, toolbarFrame, pack_toolbar =False)
    toolbar.pack(side=tkinter.LEFT)
    global graphVals
    graphVals = [[i + 1, curve[i]]  for i in range(len(curve))]

    # Area Under curve value
    region = curve[int(fromImgAUCNum.get()) - 1:int(toImgAUCNum.get())]
    resultAUC.set(np.trapz([pixelTotalVal - x for x in region]))

    # Draws show data button
    graphDataButton = tkinter.Button(lfAUC, text="Graph Data", command=OpenNewWindow)
    graphDataButton.grid(row=6, column=4, sticky="w",  pady=(10, 10), padx = (0, 5))

# Saves the graph data to a csv file
def SaveCSV():
    global graphVals
    file = tkinter.filedialog.asksaveasfile(
        initialfile="graphData.csv", 
        defaultextension=".csv",
    )

    if file is not None:
        df = pd.DataFrame(np.asarray(graphVals))
        df.columns = ['frame','value']
        df.to_csv(file.name)

# Saves the graph data to a xlsx file
def SaveExcel():
    global graphVals
    file = tkinter.filedialog.asksaveasfile(
        initialfile="graphData.xlsx", 
        defaultextension=".xlsx",
    )
    
    if file is not None:
        df = pd.DataFrame(np.asarray(graphVals))
        df.columns = ['frame','value']
        writer = pd.ExcelWriter(file.name, engine='xlsxwriter')
        df.to_excel(writer)
        writer.save()

# Opens new window with data
def OpenNewWindow():     
    # Toplevel object which will
    # be treated as a new window
    newWindow = tkinter.Toplevel(root)
 
    # sets the title of the
    # Toplevel widget
    newWindow.title("Graph Data")
 
    # sets the geometry of toplevel
    newWindow.geometry("230x230")
 
    # A Label widget to show in toplevel
    menuBar = tkinter.Menu(newWindow)
    filemenu = tkinter.Menu(menuBar, tearoff=0)
    filemenu.add_command(label="Save to csv", command=SaveCSV)
    filemenu.add_command(label="Save to xlsx", command=SaveExcel)

    menuBar.add_cascade(label="File", menu=filemenu)

    newWindow.configure(menu=menuBar)

    # Scrollbars
    outputScroll = ttk.Scrollbar(newWindow)
    outputScroll.grid(row=1, column=1, sticky="ns")

    outputSideScroll = ttk.Scrollbar(newWindow, orient=tkinter.HORIZONTAL)
    outputSideScroll.grid(row=2, column=0, sticky="ew")

    output = ttk.Treeview(newWindow, yscrollcommand=outputScroll.set, xscrollcommand=outputSideScroll.set)
    output.grid(row=1, column=0, sticky="nsew")

    outputScroll.config(command=output.yview)
    outputSideScroll.config(command=output.xview)
    output.column("#0", width=400, stretch=tkinter.NO)
    


    # deletes previous values if they exist
    #output.column("#0", width=400, stretch=tk.NO)
    for i in output.get_children():
        output.delete(i)

    rowHeaders = ["Frame", "Value"]

    # generates columns and column headers
    output['columns'] = rowHeaders
    output.column("#0", width=0, stretch=tkinter.NO)
    output.heading("#0",text="",anchor=tkinter.CENTER)
    for col in rowHeaders:
        output.column(col, anchor=tkinter.CENTER, width=100)
        output.heading(col, text=col, anchor=tkinter.CENTER)
    global graphVals
    # Generates values
    for row in range(len(graphVals)):
        output.insert(parent='',index='end',iid=row, values=graphVals[row])

if __name__ == "__main__":
    # creating main window
    root = tkinter.Tk()
    root.geometry('1100x900')   
    root.title("Tkinter App")

    # coordinates for where the top left corner of the image viewing modules will generate
    ciX = 400
    ciY = 80

    #root['cursor']='@mouse.cur'


    # The Module that holds the sliders and input for the variables GUI
    lfAnnalysis = tkinter.LabelFrame(root, text="Process Variables")
    lfAnnalysis.grid(row=1,column=0, padx=(10, 0), sticky="nwse")

    # Draws Base scale and label
    lfbaseLabel = tkinter.LabelFrame(lfAnnalysis, text="Base Count")
    lfbaseLabel.grid(row=0,column=0, columnspan=3, padx=(10,10), pady=(10,10))
    currBase = tkinter.IntVar()
    currBase.set(1)
    scaleBase = tkinter.Scale(lfbaseLabel, length=350, variable=currBase, from_=1, to=1, orient = tkinter.HORIZONTAL)
    scaleBase.grid(row=0,column=0)
    
    # Draws Difference scale and label
    lfdiffLabel = tkinter.LabelFrame(lfAnnalysis, text="Difference amount:")
    lfdiffLabel.grid(row=1,column=0, columnspan=3, padx=(10,10), pady=(10,10))
    currDiff = tkinter.IntVar()
    currDiff.set(40)
    scaleDiff = tkinter.Scale(lfdiffLabel, length=350, variable=currDiff, from_=1, to=100, orient= tkinter.HORIZONTAL)
    scaleDiff.grid(row=0,column=0)

    # Sub module used to select which images to check
    lfCheck = tkinter.LabelFrame(lfAnnalysis, text = "Check Images")
    lfCheck.grid(row=2, column=0, columnspan=2, padx=(10,10), pady=(10,10))

    # Draws Check Images UI
    labelCheckFrom = tkinter.Label(lfCheck, text="From:")
    labelCheckFrom.grid(row=0, column=0)
    labelCheckTo = tkinter.Label(lfCheck, text="To:")
    labelCheckTo.grid(row=0, column=2)
    fromImgNum = tkinter.StringVar()
    inputFrom = tkinter.Spinbox(lfCheck, from_=1, to=1, textvariable=fromImgNum, width=5)
    inputFrom.grid(row=0, column=1)
    toImgNum = tkinter.StringVar()
    inputTo = tkinter.Spinbox(lfCheck, from_=1, to=1, textvariable=toImgNum, width=5)
    inputTo.grid(row=0, column=3, padx=(0, 10), pady=(10,10))

    # Draws doGradient checkbox and label
    doGradient = tkinter.IntVar()
    doGradient.set(1)
    checkGradient = tkinter.Checkbutton(lfAnnalysis, text="Do Gradient", variable=doGradient, onvalue=1, offvalue=0)
    checkGradient.grid(row=3, column=0, sticky="w")

    # Draws doGrayscale checkbox and label
    doGrayScale = tkinter.IntVar()
    doGrayScale.set(1)
    checkGrayScale = tkinter.Checkbutton(lfAnnalysis, text="Gray Scale", variable=doGrayScale, onvalue=1, offvalue=0)
    checkGrayScale.grid(row=4, column=0, sticky="w")

    # Draws calculate button
    calculateButton = tkinter.Button(lfAnnalysis, text="Calculate", command=CalculateDiff)
    calculateButton.grid(row=2, column=1, rowspan=2, sticky="e",  pady=(10, 10), padx = (0, 5))



    # Module used to select area under curve info
    lfAUC = tkinter.LabelFrame(root, text="Area Under Curve")
    lfAUC.grid(row=2,column=0, padx=(10, 0), pady=(10, 0), sticky="nwse")

    # Draws Use ROI checkbox and label
    useROI = tkinter.IntVar()
    useROI.set(0)
    checkUseROI = tkinter.Checkbutton(lfAUC, text="Use ROI", variable=useROI, onvalue=1, offvalue=0)
    checkUseROI.grid(row=2, column=3, sticky="w")

    # Draws Use Result Image and label
    useResult = tkinter.IntVar()
    useResult.set(1)
    checkUseResult = tkinter.Checkbutton(lfAUC, text="Use Result Image", variable=useResult, onvalue=1, offvalue=0)
    checkUseResult.grid(row=2, column=2, sticky="w")

    # Draws calculate button
    calculateAUCButton = tkinter.Button(lfAUC, text="Calculate", command=ConstructGraph)
    calculateAUCButton.grid(row=2, column=4, sticky="w",  pady=(10, 10), padx = (0, 5))

    # Draws AUC value
    labelAUCTitle = tkinter.Label(lfAUC, text="Area Under Curve:")
    labelAUCTitle.grid(row=3, column=3, sticky="e")
    resultAUC = tkinter.StringVar()
    resultAUC.set("NaN")
    labelAUC = tkinter.Entry(lfAUC, textvariable=resultAUC, width=10 ,state='readonly')
    labelAUC.grid(row=3,column=4, sticky="w")


    # Sub module used to select which images to check
    lfAUCCheck = tkinter.LabelFrame(lfAUC, text = "Check Images")
    lfAUCCheck.grid(row=3, column=0, columnspan=3, padx=(10,10), pady=(10,10))

    # Draws Check Images UI
    labelAUCCheckFrom = tkinter.Label(lfAUCCheck, text="From:")
    labelAUCCheckFrom.grid(row=0, column=0)
    labelAUCCheckTo = tkinter.Label(lfAUCCheck, text="To:")
    labelAUCCheckTo.grid(row=0, column=2)
    fromImgAUCNum = tkinter.StringVar()
    inputAUCFrom = tkinter.Spinbox(lfAUCCheck, from_=1, to=1, textvariable=fromImgAUCNum, width=5)
    inputAUCFrom.grid(row=0, column=1)
    toImgAUCNum = tkinter.StringVar()
    inputAUCTo = tkinter.Spinbox(lfAUCCheck, from_=1, to=1, textvariable=toImgAUCNum, width=5)
    inputAUCTo.grid(row=0, column=3, padx=(0, 10), pady=(10,10))


    # Module that contains ability to load files holds information about them
    lfImageInput = tkinter.LabelFrame(root, text="Import Files")
    lfImageInput.grid(row=0, column=0, padx=(10, 10), sticky="nwse")

    # Creates button to start file explorer for images needed to be analyzed
    buttonGetPNGs = tkinter.Button(lfImageInput, text="Find Images", command=BrowseFiles)
    buttonGetPNGs.grid(row=0, column=3, padx=(27,5), pady=(20,15))

    # Label informing the amount of images loaded
    labelImagesLoaded = tkinter.Label(lfImageInput, text="Images Loaded:")
    labelImagesLoaded.grid(row=0, column=0)
    loadedNum = tkinter.StringVar()
    loadedNum.set("NaN")
    labelImagesNum = tkinter.Entry(lfImageInput, textvariable=loadedNum, width=5, state='readonly')
    labelImagesNum.grid(row=0, column=1)


    # Module that contains ability to save results and holds information about result image
    lfSave= tkinter.LabelFrame(root, text="Result")
    lfSave.grid(row=0, column=1, padx=(10,10), sticky="nwse")

    # Draws number of pixels that fulfull the requirement
    labelResultingNumTitle = tkinter.Label(lfSave, text="Number of Pixels:")
    labelResultingNumTitle.grid(row=0, column=0)
    resultNum = tkinter.StringVar()
    resultNum.set("NaN")
    labelResultingNum = tkinter.Entry(lfSave, textvariable=resultNum,width=5 ,state='readonly')
    labelResultingNum.grid(row=0,column=1)

    # Draws total number of pixels in image
    labelTotalNumTitle = tkinter.Label(lfSave, text="Initial non-Empty Pixels:")
    labelTotalNumTitle.grid(row=1, column=0)
    totalNum = tkinter.StringVar()
    totalNum.set("NaN")
    labelTotalNum = tkinter.Entry(lfSave, textvariable=totalNum,width=5 ,state='readonly')
    labelTotalNum.grid(row=1, column=1)

    # Draws checkbox and label
    doAlpha = tkinter.IntVar()
    doAlpha.set(0)
    checkAlphat = tkinter.Checkbutton(lfSave, text="Save Black as Transparent", variable=doAlpha, onvalue=1, offvalue=0)
    checkAlphat.grid(row=0, column=4, sticky="w")

    # Draws save button
    saveButton = tkinter.Button(lfSave, text="Save to file", command=SaveToFile)
    saveButton.grid(row=1, column=4, pady=(0,10), padx=(10,10), sticky="se")

    # Draws current image scale and its label
    labelCurrImg = tkinter.Label(root, text="Current Image:")
    labelCurrImg.place(x=ciX+0, y=ciY+20)
    currImageIndex = tkinter.IntVar()
    scaleCurrImg = tkinter.Scale(root, from_=1, to=1, variable=currImageIndex, orient = tkinter.HORIZONTAL, command=ScaleSizeSlider)
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

    # creates the canvas images and some overlays are on
    canvasImages = tkinter.Canvas(lfImages, width=1600, height=800)
    canvasImages.pack(side="left")

    # adds image objects to the canvas
    imageDisplay = canvasImages.create_image(10, 10, anchor=NW, image="")
    imageFinal = canvasImages.create_image(50, 10, anchor=NW, image="")
    
    # binds the click events for the images 
    canvasImages.tag_bind(imageDisplay, "<B1-Motion>", DragOnImage)
    canvasImages.tag_bind(imageDisplay, "<Button-1>", ClickOnImage)
    
    canvasImages.tag_bind(imageFinal, "<B1-Motion>", DragOnResult)
    canvasImages.tag_bind(imageFinal, "<Button-1>", ClickOnResult)

    canvasImages.tag_bind(imageDisplay, "<ButtonRelease-1>", ReleasedOnImage)
    canvasImages.tag_bind(imageFinal, "<ButtonRelease-1>", ReleasedOnResult)
    

    canvasImages.tag_bind(imageDisplay, "<Enter>", ImageEnter)
    canvasImages.tag_bind(imageDisplay, "<Leave>", ImageExit)
    canvasImages.tag_bind(imageFinal, "<Enter>", ImageEnter)
    canvasImages.tag_bind(imageFinal, "<Leave>", ImageExit)
    
    selectionSquareDisplay = canvasImages.create_rectangle(X_OFFSET, Y_OFFSET, X_OFFSET, Y_OFFSET, outline="white", state=tkinter.DISABLED)
    selectionSquareFinal = canvasImages.create_rectangle(50, Y_OFFSET, 50, Y_OFFSET, outline="white", state=tkinter.DISABLED)

    canvasImages.delete(selectionSquareDisplay)
    canvasImages.delete(selectionSquareFinal)

    root.bind("<Shift_L>", ShiftDown)
    root.bind("<KeyRelease-Shift_L>", ShiftUp)

    root.after(100, loop)
    root.mainloop()