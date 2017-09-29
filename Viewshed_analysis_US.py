#!/usr/bin/env python

import grass.script as gscript
import sys
import os
from math import pi, cos

writer = sys.stdout.write

class viewshed:
    '''Compute, analyze and output metrics for viewsheds'''

    def __init__(self,line):
        ''' initialize the parameters and output names based on the coordinte
        file lines '''

        # Landcover Categories
        self.landuse={11:"Open_Water", 12:"Perrenial_snow", 21:"Developed_open",
        22:"Developed_low",23:"Developed_Med", 24:"Developed_High",
        31:"Barren", 41:"Decidous", 42:"Evergreen", 43:"Mixed", 51:"Dwarf_scrub",
        52:"Shrub", 71:"Grassland", 72:"Sedge", 73:"Lichens", 74:"Moss",
        81:"Pasture_Hay", 82:"Cultivated_crops", 90:"Woodey_Wetlands",
        95:"Emergent_herbacous_Wetland"}

        # view distance Categories

        # Get coordinates of the viewpoint
        print line.split(',')
        self.Xcoord = line.split(',')[0]
        self.Ycoord = line.split(',')[1]
        self.index = line.split(',')[2]
        self.panoID = line.split(',')[3]


        # Name of the landcover dataset
        self.luse_raster='NLCD_refined'
        # Name of the DSM dataset
        self.in_raster = 'DSM_water'

        # Outputs : elevation viewshed, visible landcover, binary viewshed,
        # observer viewpoint rasterized, distance map, depth viewshed

        self.out_landuse= "luse_out"
        self.out_binary= 'binary'
        self.tmp_point = "tmp_point"
        self.tmp_far = "tmp_far"
        self.tmp_mid = "tmp_mid"
        self.tmp_near = "tmp_near"

        gscript.write_command('v.in.ascii', input='-',
                            stdin='%s|%s' % (self.Xcoord,self.Ycoord),
                            output=self.tmp_point, overwrite = True)

        gscript.run_command('v.buffer', input=self.tmp_point, output=self.tmp_far,
                            distance = .05, overwrite = True)

        gscript.run_command('v.buffer', input=self.tmp_point, output=self.tmp_mid,
                            distance = .025, overwrite = True)

        gscript.run_command('v.buffer', input=self.tmp_point, output=self.tmp_near,
                            distance = .01, overwrite = True)

    def changeRegion(self, vector):

        gscript.run_command('g.region', vector= vector)

    def BasicViewshed(self):
         """ computes viewshed, extent, depth """

         # Compute viewshed #
         gscript.run_command('r.viewshed', input = self.in_raster,
            output = self.out_binary, max_distance = 5000,
            coordinates = [self.Xcoord, self.Ycoord],
            observer_elevation = 2, target_elevation = 1, memory = 2122547200,
            overwrite = True, flags = 'bc')

         # Combine viewshed with landcover
         gscript.run_command('r.mapcalc',
            expression='{0}=if({1}==1,{2},null())'.
            format(self.out_landuse, self.out_binary,
            self.luse_raster),overwrite=True)

         # import the classification category from landcover
         gscript.run_command('r.category', map=self.out_landuse,
            raster = self.luse_raster)

    def CompositionMetrics(self):

        '''Overlay landcover with viewshed, calculate visible cover,
        and return percentage of landcover classes in viewshed
        '''
        ## Compute statistics ##
        stat=gscript.parse_command('r.stats', input=self.out_landuse,
                        flags='apn', separator='comma',overwrite=True)

        cleanDic={}
        areaList=[]
        totarea = 0
        for item in stat.keys():
            cat=int(item.split(",")[0])
            area= item.split(",")[1]
            percent= item.split(",")[2]
            cleanDic[cat]= percent.strip("%").strip("u")
            totarea += float(area)
            print totarea

        areaList=[]
        for item in sorted(self.landuse.keys()):
            if item in cleanDic.keys():
                percent = cleanDic[item]
                areaList.append(str(percent))
            else:
                areaList.append("0")
        areaList.append(str(totarea))

        return areaList

    def WriteStats(self,basic=False, composition=False,write=False):
        '''Write statistics to the output file based on the selected options '''

        if basic:
            self.changeRegion(self.tmp_far)
            self.BasicViewshed()

        if composition:
           compOut1=self.CompositionMetrics()
           self.changeRegion(self.tmp_mid)
           compOut2=self.CompositionMetrics()
           self.changeRegion(self.tmp_near)
           compOut3=self.CompositionMetrics()


        else:
            compOut= [str(i*0) for i in range (len(self.landuse.keys()))]

        if write:
            write = (
                    str(self.index).strip("\n") + "\t" + str(self.panoID).strip("\n")
                    + "\t" + ("\t").join(compOut1) +
                    "\t"+ ("\t").join(compOut2) + "\t" + ("\t").join(compOut3) + "\n"
                    )
            return write

    def MakeHeader(self):
        '''Create outputfile header'''

        comp = [self.landuse[i] for i in sorted(self.landuse.keys())]
        compHeader = "\t".join(comp) + "\t" + "extent"
        header = ("index" + "\t" + "panoID" + "\t" + compHeader + "\t"  +
                compHeader + "\t" + compHeader + "\n")

        return header

def runViewshed(file, output):
    ''' read the comma seperated inputfile and create the outputfile '''

    outFile = open(output, 'w')
    coordFile = open(file, 'r')
    lineCount= sum(1 for _ in coordFile)
    coordFile.seek(0)

    for counter,line in enumerate(coordFile.readlines()):

        if counter == 0:
          outFile.write(viewshed(line).MakeHeader())

        try:
            write=viewshed(line).WriteStats(basic= True,composition= True,write=True)
            outFile.write(write)

        except :
            print "viewshed {0} encountered an error".str(format(self.index))

    outFile.close()

if __name__ == '__main__':

    runViewshed("input_coords.txt","output_metrics.txt")

