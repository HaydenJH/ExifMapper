import os
import shutil
import sys
from pygeocoder import Geocoder
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from BeautifulSoup import BeautifulSoup as bs
import urlparse
from urllib2 import urlopen
from urllib import urlretrieve
from glob import glob

def listToHTMLFile(dataList): # Formatting the EXIF data we care about into an HTML doc, not caring too much for making source pretty though =(
	out = open("data.html", "w")
	divOpen = "<div style=\"border-style:solid; border-width:small; border-color:black; padding:10px;\">"
	divClose = "</div><br />"
	htmlCode = ""	
	htmlHead = "<html> \
				<head><title>Exif Data</title></head> \
				<body style=\"background: #D8D8D8; color: black;\">"
	htmlFoot = r"</body></html>"
	
	for b in range(len(dataList)):
		if "GPSInfo" in dataList[b]:
			latitude 	= getGPSLat(dataList[b])
			longitude 	= getGPSLong(dataList[b])
			location 	= pygeo.reverse_geocode(latitude, longitude)
			
			gMap1 = "<br /> <img src = http://maps.googleapis.com/maps/api/staticmap?center=" + str(latitude) + "," + str(longitude) + "&zoom=12&size=450x450&sensor=false&format=gif&markers=color:red%7Clabel:X%7C" +str(latitude) +"," +str(longitude)+" />"
			gMap2 = "<img src = http://maps.googleapis.com/maps/api/staticmap?center=" + str(latitude) + "," + str(longitude) + "&maptype=hybrid&zoom=18&size=450x450&sensor=false&format=gif&markers=color:red%7Clabel:X%7C" +str(latitude) +"," +str(longitude)+" /><br />"
			
			gps = "<p><span style=\"text-decoration: underline;\">GPS info:</span><br /> Latitude = " + str(latitude) + "<br />Longitude = " + str(longitude) + "<br /> Location =  " + str(location)
		else: 
			gps 	= "<br />No GPS data found"
			gMap1 	= ""
			gMap2 	= ""	
		
		filename = "<p style =\"color:black; font-weight:strong; font-size:24\"> Image Filename: " + dataList[b]["FileName"] + " </p>"
		
		if "Model" in dataList[b]:
			model = "Camera Model = " + dataList[b]["Model"] + "<br />"
		else:
			model = "Model = Model data not found <br />"
		
		if "Make" in dataList[b]:
			make = "Camera Make = " + dataList[b]["Make"] + "<br />"
		else:
			make = "Camera Make = Camera make data not found <br />"
		
		if "DateTimeOriginal" in dataList[b]:
			dateTime = "Date and time photo taken (YYYY/MM/DD) = " + dataList[b]["DateTimeOriginal"] + "<br />"
		else:
			dateTime = "Date and Time taken = No date/time found <br />"
		
		tn = os.path.splitext(dataList[b]["FileName"])[0] + ".thumb"
		thumbnail = "<img src=\"" + thumbsfolder + tn + " \"/> <br />"
		
		htmlCode +=  divOpen + filename + thumbnail +make + model + dateTime + gps + gMap1 + gMap2 + divClose
		
	out.write(htmlHead + htmlCode + htmlFoot)
	out.close()
	print("\n Data html file created")
	
def getExifData(file):
	imgDir 	= directory + file
	
	if not os.path.exists(thumbsfolder):
   		os.makedirs(thumbsfolder)
   	try:
		i = Image.open(imgDir)
	except IOError:
		return
	tn = os.path.splitext(file)[0] + ".thumb"
	
	try:
		i.thumbnail(size, Image.ANTIALIAS)
		i.save(thumbsfolder + tn, "JPEG")
	except IOError:
		print "failed creating thumbnail"
		
	info = i._getexif()
	ret = {}
	for tag, val in info.items():
		decoded = TAGS.get(tag, tag)
		if decoded in requiredExifData: #filter out everything we don't want
			ret[decoded] = val
	
	ret["FileName"] = file
	return ret


def getGPSLat(exif):
	Nsec = exif['GPSInfo'][2][2][0] / float(exif['GPSInfo'][2][2][1])
	Nmin = exif['GPSInfo'][2][1][0] / float(exif['GPSInfo'][2][1][1])
	Ndeg = exif['GPSInfo'][2][0][0] / float(exif['GPSInfo'][2][0][1])
		
	if exif['GPSInfo'][1] == 'S':
		Nmult = -1
	else:
		Nmult = 1
	lat = Nmult * (Ndeg + (Nmin + Nsec/60.0)/60.0)
	return lat

	
def getGPSLong(exif):
	Wsec = exif['GPSInfo'][4][2][0] / float(exif['GPSInfo'][4][2][1])
	Wmin = exif['GPSInfo'][4][1][0] / float(exif['GPSInfo'][4][1][1])
	Wdeg = exif['GPSInfo'][4][0][0] / float(exif['GPSInfo'][4][0][1])
		
	if exif['GPSInfo'][3] == 'W':
		Wmult = -1
	else:
		Wmult = 1
	
	long = Wmult * (Wdeg + (Wmin + Wsec/60.0)/60.0)
	return long


def parseDirectory():
	for i in range(len(dirList)):
		print("Discovering image: " + dirList[i])
		if "." in dirList[i]:			# make sure we are only getting files (not dirs etc)
			extension = dirList[i].split(".")[-1].strip().lower()
			if extension in allowedFiles:  #check to see if file is right type
				fileList.append(dirList[i])
				

	for x in range(len(fileList)): # creating a 2d dictionary of exif info
		exifList.append(getExifData(fileList[x]))

def parseURL(url):
    soup = bs(urlopen(url))
    parsed = list(urlparse.urlparse(url))

    for image in soup.findAll("img"):
        print "Discovering image: %(src)s" % image
        filename = image["src"].split("/")[-1]
        parsed[2] = image["src"]
       	
       	outfolder = os.path.join(os.getcwd(),"imgs from web")
       	if not os.path.exists(outfolder):
   			 os.makedirs(outfolder)

        outpath = os.path.join(outfolder, filename)
        
        if image["src"].lower().startswith("http"):
        	urlretrieve(image["src"], outpath)
        else:
            urlretrieve(urlparse.urlunparse(parsed), outpath)

# def cleanUp():
# 	for f in os.listdir(thumbsfolder):
# 		filePath = os.path.join(thumbsfolder, f)
#     	try:
#        		if os.path.isfile(filePath):
#            		os.unlink(filePath)
#     	except Exception, e:
#        		print e
############################ End of function defs #########################################

allowedFiles 		= ["jpg", "jpeg", "tiff", "wav", "JPG", "JPEG", "WAV"]
requiredExifData 	= ["GPSInfo", "Model","Make","DateTimeOriginal"]

thumbsfolder = os.path.join(os.getcwd(),"thumbs\\") 
size 		= 200,200 #thumbnail size

pygeo 		= Geocoder()

exifList 	= []
fileList 	= []

directory = raw_input("Enter the directory or website of images: ")

# if directory == "/cleanup":
# 	if os.path.exists(thumbsfolder):
# 		cleanUp()
# 		print("Content deleted from thumbs and web images folders")
# 		sys.exit()
if directory.lower().startswith("http"): #if url is entered
	parseURL(directory)
	directory = os.path.join(os.getcwd(),"imgs from web\\")
	dirList = os.listdir(directory)
	parseDirectory()
else:
	#Add a single backslash to end of directory for when we concat the image names to it
	if directory[-1] != "\\":
		directory = directory + "\\"
	dirList = os.listdir(directory)
	parseDirectory()


listToHTMLFile(exifList)
	
	

	
	





