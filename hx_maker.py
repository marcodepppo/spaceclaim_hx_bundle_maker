# Python Script, API Version = V20 Beta
import math
import sys


#NB this script works on a yz plane

#parameters

Ntubes = 8466
#Ntubes = 30
OD = 9.58 #mm
tubeTks = 0.89 #mm 
straightLen = 2700 #mm
pitch = 11.98 #mm
passPlateTcks = 6.5 #mm
centerPlaneDist = passPlateTcks + pitch #can be adjusted
shellRadius = 870 #mm
radiusLimit = 700 #mm

pipeFolderName = "HX_BUNDLE_PIPES"
waterFolderName = "HX_BUNDLE_WATER"


#FUNCTIONS

def getParentComponents(body):
    level = body
    componentsVector = List[IDocObject]()
        
    while True:

        if level.Parent.Parent:
            level = level.Parent.Parent
            #print level.GetType()
            #print level.GetName()
            componentsVector.Add(level)

        else:
                
            level = level.Parent
            #print level.GetType()
            #print level.GetName()
            componentsVector.Add(level)

            break

  #  for element in componentsVector:
  #      print element.GetName()
    return componentsVector


def pierce_base(base, pipe):
    
    selBase = Selection.Create(base)
    selPipe = Selection.Create(pipe)
    options = MakeSolidsOptions()
    result = Combine.Intersect(selBase, selPipe, options)
    createdSolids = result.GetCreated[IDesignBody]() 
    modifiedSolids = result.GetModified[IDesignBody]()

    delSel = Selection.Create(createdSolids)
    Delete.Execute(delSel)

    return 
    
def remove_pipe_intersection(pipeExt, pipeInn):
    
    selPipeExt = Selection.Create(pipeExt)
    selPipeInn = Selection.Create(pipeInn)
    options = MakeSolidsOptions()
    result = Combine.Intersect(selPipeExt, selPipeInn, options)
    createdSolids = result.GetCreated[IDesignBody]()
    for body in createdSolids:
        delSel = Selection.Create(body)
        Delete.Execute(delSel)
        return
    

def createTube(startCoords, endCoords,centerTorusCoords,endCoords2,startCoords2,diameter):
    
    #define points
    startPoint = Point.Create(*startCoords)
    endPoint = Point.Create(*endCoords)
    centerTorusPoint = Point.Create(*centerTorusCoords)
    startPoint2 = Point.Create(*startCoords2)
    endPoint2 = Point.Create(*endCoords2)
    #define lines
    resultLine1 = SketchLine.Create(startPoint, endPoint)
    resultLine2 = SketchLine.Create(startPoint2, endPoint2)
    senseClockWise = True
    resultTorusLine = SketchArc.Create3PointArc(endPoint2, endPoint,centerTorusPoint)
    #create circles
    sectionPlane = Plane.Create(Frame.Create(startPoint, 
    -Direction.DirZ, 
    Direction.DirY))
    resultCircleLarge = SketchCircle.Create(startPoint,diameter, sectionPlane)
    #fill circles
    planeSel = Selection.Create(resultCircleLarge.GetCreated[IDesignCurve]())
    secondarySelection = Selection.Empty()
    options = FillOptions()
    resultCirclSurf = Fill.Execute(planeSel, secondarySelection, options, FillMode.ThreeD, None)
    Delete.Execute(planeSel)
    #extrude circles
    faceSel = Selection.Create(resultCirclSurf.GetCreated[IDesignFace]())
    trajectories = Selection.Create(resultLine1.GetCreated[IDesignCurve]()[0],resultLine2.GetCreated[IDesignCurve]()[0],resultTorusLine.GetCreated[IDesignCurve]()[0])
    options = SweepCommandOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    options.Select = True
    resultSweep = Sweep.Execute(faceSel, trajectories, options, None)
    Delete.Execute(trajectories)
    extrudedBody = resultSweep.GetCreated[IDesignBody]()[0]
    
    return extrudedBody





#MAIN

# select base of the bundle
inputFaces = Selection.GetActive().GetItems[IDesignFace]() 
circleBase = inputFaces[0]

baseBody = circleBase.GetAncestor[IDesignBody]()
parentComps = getParentComponents(baseBody)

#create Folders
resultComp = ComponentHelper.CreateAtComponent(parentComps[1], pipeFolderName)
compPipes = resultComp.CreatedComponents[0]
resultComp2 = ComponentHelper.CreateAtComponent(parentComps[1], waterFolderName)
compWater = resultComp2.CreatedComponents[0]

#find base center
baseCenter =  circleBase.GetFacePoint(0.5,0.5)
baseNormal =  circleBase.GetFaceNormal(0.5,0.5)
print(baseNormal)
#DatumPointCreator.Create(baseCenter)

#find base radius
radius = circleBase.Edges[0].Shape.Geometry.Radius

#find pipes centers
dx = 2 * (pitch*0.001) * math.cos(math.radians(30))
dy = (pitch*0.001) * math.sin(math.radians(30))
print(dy)
iCounter = 0
jCounter = 0

extrudedBodyList = []
extrudedBodyInnerList = []

for i in range(Ntubes/2):
    if (i*2) % 100 == 0:
        print "i = ", 2*i
    yCoord = jCounter * dy + (centerPlaneDist *0.001)
    if jCounter % 2 == 0:
        xCoord = iCounter * dx + dx/2
        xCoordMirror = iCounter * dx + dx/2
    else:
        #xCoord = iCounter * dx + 0.5*(pitch*0.001) + dx/2
        #xCoordMirror = iCounter * dx - 0.5*(pitch*0.001) + dx/2
        xCoord = iCounter * dx + 0.5*(dx) + dx/2
        xCoordMirror = iCounter * dx - 0.5*(dx) + dx/2
    radiusCoord = (xCoord**2 + yCoord**2)**0.5
    
    if radiusCoord > (radiusLimit*0.001):
        jCounter += 1
        iCounter = 0
        continue
    else:
        iCounter += 1
    
    
    #define point Coordinates
    startCoords = [baseCenter.X, baseCenter.Y + yCoord, baseCenter.Z + xCoord]
    endCoords = [baseCenter.X - (straightLen*0.001), baseCenter.Y + yCoord, baseCenter.Z + xCoord]
    centerTorusCoords = [baseCenter.X - (straightLen*0.001) - yCoord, baseCenter.Y , baseCenter.Z + xCoord]
    endCoords2 = [baseCenter.X - (straightLen*0.001), baseCenter.Y - yCoord, baseCenter.Z + xCoord]
    startCoords2 = [baseCenter.X, baseCenter.Y - yCoord, baseCenter.Z + xCoord]
    
        
    extrudedBody = createTube(startCoords, endCoords,centerTorusCoords,endCoords2,startCoords2,OD*0.001/2)
    extrudedBodyInner = createTube(startCoords, endCoords,centerTorusCoords,endCoords2,startCoords2,(OD*0.001/2 - tubeTks*0.001))
    #pierce base

    pierce_base(baseBody, extrudedBodyInner)
    pierce_base(baseBody, extrudedBody)
    
    # remove intersection
    remove_pipe_intersection(extrudedBody, extrudedBodyInner)
    extrudedBodyList.append(extrudedBody)
    extrudedBodyInnerList.append(extrudedBodyInner)

    
    
   ###### MIRROR ######
   #define points coordinates Mirror
    startCoordsMirror = [baseCenter.X, baseCenter.Y + yCoord, baseCenter.Z - xCoordMirror]
    endCoordsMirror = [baseCenter.X - (straightLen*0.001), baseCenter.Y + yCoord, baseCenter.Z - xCoordMirror]
    centerTorusCoordsMirror = [baseCenter.X - (straightLen*0.001) - yCoord, baseCenter.Y , baseCenter.Z - xCoordMirror]
    endCoords2Mirror = [baseCenter.X - (straightLen*0.001), baseCenter.Y - yCoord, baseCenter.Z - xCoordMirror]
    startCoords2Mirror = [baseCenter.X, baseCenter.Y - yCoord, baseCenter.Z - xCoordMirror]
  

    extrudedBodyMirror = createTube(startCoordsMirror, endCoordsMirror,centerTorusCoordsMirror,endCoords2Mirror,startCoords2Mirror,OD*0.001/2)
    extrudedBodyInnerMirror = createTube(startCoordsMirror, endCoordsMirror,centerTorusCoords,endCoords2Mirror,startCoords2Mirror,(OD*0.001/2 - tubeTks*0.001))
       
    pierce_base(baseBody, extrudedBodyInnerMirror)
    pierce_base(baseBody, extrudedBodyMirror)
   # remove intersection
    remove_pipe_intersection(extrudedBodyMirror, extrudedBodyInnerMirror)
    
    extrudedBodyList.append(extrudedBodyMirror)
    extrudedBodyInnerList.append(extrudedBodyInnerMirror)

    
selExtrudedBody = Selection.Create(extrudedBodyList)
selExtrudedBodyInner = Selection.Create(extrudedBodyInnerList)
ComponentHelper.MoveBodiesToComponent(selExtrudedBody,  compPipes, False)
ComponentHelper.MoveBodiesToComponent(selExtrudedBodyInner,  compWater, False)
    
    
    
    