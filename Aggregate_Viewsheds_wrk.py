#!/usr/bin/env python

#import grass.script as gscript
import sys
import os
from math import pi, cos, sqrt

rasterFile = "D:\DOWNLOADS\\viewshedZonelist.txt"
regionFile = "D:\\Google_drive\\Projects_manuscripts\\US_Viewsheds\\regoin_shapeFile\\region_coordinates.txt"
outFile = "D:\\Google_drive\\Projects_manuscripts\\US_Viewsheds\\regoin_shapeFile\\region_coordinates_out.txt"

def getBinaryList(rastFile):
    """ recieves a comma seperated file with region index and list of binary viewsheds and returns a dictionary with
    region index as value and a list of binary viewsheds as key"""
    readFile = open(rastFile, 'r')
    dic = {}
    for line in readFile.readlines():
        index = line.split(',')[0]
        lineParse = line.split(',')[1:]
        inputList=["binary"+ i.strip(" ").strip("\n") for i in lineParse]
        dic[index] = inputList
    return dic

# this line prints the binary list of the region with index value of 2
#print getBinaryList(rasterFile)["2"]



def getRegionCoords(regionFile, offset):
""" recieves a comma seperated ascii with point coordinates
and offset value and returns a dictionary with
point index as value and region coordiante as key"""

    readFile = open(regionFile, 'r')
    dicCoords ={}
    for line in readFile.readlines():
        lineParse = line.split(',')
        index = lineParse[2]
        x = float(lineParse[0])
        y = float(lineParse[1])
        dim = sqrt(float(lineParse[3].strip("\n")))
        north = y + dim/2 + offset
        south = y - dim/2 - offset
        east = x + dim/2 + offset
        west = x - dim/2 - offset
        dicCoords[index] = (north, south, east, west)
    return dicCoords

# this line tests the region coordinates of a sample point with index 2
print getRegionCoords(regionFile,5000)["2"]
