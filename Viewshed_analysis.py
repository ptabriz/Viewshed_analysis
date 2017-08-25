#!/usr/bin/env python

import grass.script as gscript
import sys
import os

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
        self.depthMetric=["max", "firstQ", "medianQ", "thirdQ", "sd", "covar"]

        # Get coordinates of the viewpoint
        self.Xcoord = split=line.split(',')[0]
        self.Ycoord = split=line.split(',')[1]
        self.index = line.split(',')[2]

        # Size of the computational Region
        north = float(self.Ycoord) + 10000
        south = float(self.Ycoord) - 10000
        east = float(self.Xcoord) + 10000
        west = float(self.Xcoord) - 10000

        # Name of the landcover dataset
        self.luse_raster='NLCD_finall'
        # Name of the DSM dataset
        self.in_raster = 'DSM_all'
        # Name of the observer raster = observation vector points rasterized
        self.observerRaster= 'observer_raster_2'

        # Outputs : elevation viewshed, visible landcover, binary viewshed,
        # observer viewpoint rasterized, distance map, depth viewshed

        self.out_viewshed = 'viewshed' + str(int(self.index))
        self.out_landuse= "luse_out_" + str(int(self.index))
        self.out_binary= 'binary' + str(int(self.index))
        self.out_observerCell= 'obcell'+ str(int(self.index))
        self.out_distance= 'distance'+ str(int(self.index))
        self.out_depth= 'depth'+ str(int(self.index))

        # observer viewpoint rasterized, distance map, depth viewshed
        gscript.run_command('g.region',n=north , s=south, e= east, w=west, flags='p')


    def BasicViewshed(self):
         """ computes viewshed, extent, depth """

         # Compute viewshed #
         gscript.run_command('r.viewshed', input=self.in_raster,
            output=self.out_viewshed, max_distance=3000,
            coordinates=[self.Xcoord,self.Ycoord],
            observer_elevation=2, target_elevation=1, memory=2122547200,
            overwrite=True, flags='ec')

         # make binary viewsheds, compute focal statistics, compute object clumps #
         gscript.run_command('r.mapcalc',expression='{0}=if({1},1,0)'.
            format(self.out_binary, self.out_viewshed), overwrite=True)
         return self.out_binary

    def DepthViewshed(self):
        ''' create a distance raster for the location, Overlay binary  viewshed
        with distance raster to acquire depth raster, calculate the distance stats
        '''

        ## create a single cell raster for observer location ##
        gscript.run_command('r.mapcalc', expression='{0}=if({1}=={2},1,null())'
                    .format(self.out_observerCell, self.observerRaster,
                    int(self.index)),overwrite=True)

        ## create distance raster (flag m for METRIC units !) ##
        gscript.run_command('r.grow.distance', input=self.out_observerCell,
                    distance=self.out_distance, overwrite=True, flags='m')

         ## create viewshed_depth raster
        gscript.run_command('r.mapcalc', expression='{0}=if({1},{2},null())'
                    .format(self.out_depth,self.out_binary,self.out_distance),
                    overwrite=True)

         ## create viewshed_depth raster
        stat_depth=gscript.parse_command('r.univar',
                                        map=self.out_depth, flags='ge',
                                        separator='comma',overwrite=True)

        max = str(stat_depth.values()[2])
        sd = str(stat_depth.values()[9])
        firstQ = str(stat_depth.values()[0])
        medianQ = str(stat_depth.values()[5])
        thirdQ = str(stat_depth.values()[13])
        covar = str(stat_depth.values()[11])
        depthList = [max,firstQ,medianQ,thirdQ,sd,covar]

        return depthList

    def CompositionMetrics(self):

        '''Overlay landcover with viewshed, calculate visible cover,
        and return percentage of landcover classes in viewshed
        '''

        # Combine viewshed with landcover
        gscript.run_command('r.mapcalc',
                        expression='{0}=if({1},{2},null())'.
                        format(self.out_landuse, self.out_viewshed,
                        self.luse_raster),overwrite=True)

        # import the classification category from landcover
        gscript.run_command('r.category', map=self.out_landuse,
                        raster=self.luse_raster)

        # import the color classification category from landcover
        gscript.run_command('r.colors',map = self.out_landuse,
                        raster=self.luse_raster)

        ## Compute statistics ##
        stat=gscript.parse_command('r.stats', input=self.out_landuse,
                        flags='an', separator='comma',overwrite=True)

        cleanDic={}
        areaList=[]

        for item in stat.keys():
            cat=int(item.split(",")[0])
            area= item.split(",")[1]
            cleanDic[cat]=float(area)
        totarea=sum(cleanDic.values())

        areaList=[]
        for item in sorted(self.landuse.keys()):
            if item in cleanDic.keys():
                percent= (cleanDic[item]/totarea)*100
                areaList.append(str(percent))
            else:
                areaList.append("0")
        areaList.append(str(totarea))
        return areaList


    def WriteStats(self,basic=False, composition=False,Depth=False,write=False):
        '''Write statistics to the output file based on the selected options '''

        if basic:
            self.BasicViewshed()

        if composition:
           compOut=self.CompositionMetrics()
        else:
            compOut= [str(i*0) for i in range (len(self.landuse.keys()))]

        if Depth:
           depthOut= self.DepthViewshed()

        if write:
            write= str(self.index).strip("\n")+ "\t"+("\t").join(compOut)+ "\t"+ ("\t").join(depthOut)+"\n"
            return write

    def MakeHeader(self):
        '''Create outputfile header'''

        comp = [self.landuse[i] for i in sorted(self.landuse.keys())]
        compHeader = "\t".join(comp) + "\t" + "extent"
        depthHeader = "\t".join(self.depthMetric)
        header = "index" + "\t" + compHeader + "\t" + depthHeader + "\n"

        return header

def combineVshed(file):
    '''Combine viewshed using r.series'''

    north=1040040
    south=30000
    west= 1860000
    east=3055020

    coordFile = open(file, 'r')

    coordDic={}


    outputList=["test_regionvert_1hor_{0}_comb".format(i) for i in range(1,20)]

    gscript.run_command('g.region',n=north+ 10000 , s=south-10000,
    e= east+ 10000, w=west-10000, flags='p')

    inputList=[str(",".join(outputList)).replace("\n","")]

    gscript.run_command('r.series', input=(inputList), output="binary_comb_final"
    , method="sum",overwrite=True,flags='z')



def runViewshed(file, output):
    ''' read the comma seperated inputfile and create the outputfile '''

    outFile = open(output, 'w')
    coordFile = open(file, 'r')
    lineCount= sum(1 for _ in coordFile)
    coordFile.seek(0)

    for counter,line in enumerate(coordFile.readlines()):

        if counter==0:
          outFile.write(viewshed(line).MakeHeader())

        try:
           write=viewshed(line).WriteStats(basic=True,composition=True,Depth=True,write=True)
           outFile.write(write)
        except:
           error="Viewshed {0} were not processed".format(line.split(',')[2]) + "\n"
           outFile.write(error)
           print error

    outFile.close()

if __name__ == '__main__':

    runViewshed("point_coords.txt", outfile)
    # combineVshed ('D:\\ptabriz\\scraping\\points_coords.txt')
