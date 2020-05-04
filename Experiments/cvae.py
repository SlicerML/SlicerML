"""

pip_install('cvae')

path = "/Users/pieper/slicer/latest/SlicerML/Experiments/cvae.py"
exec(open(path, "r").read())

"""

try:
    mrHead = slicer.util.getNode("MRHead")
except slicer.util.MRMLNodeNotFoundException:
    import SampleData
    mrHead = SampleData.downloadSample("MRHead")


import numpy
import random

def sliceTiles(volume, tileSize):
    array = slicer.util.array(volume.GetID())
    labels = []
    slices, height, width = array.shape
    rows = int(height/tileSize)
    columns = int(width/tileSize)
    tiles = numpy.zeros([slices*rows*columns, tileSize*tileSize])
    tileIndex = 0
    for slice in range(slices):
        for row in range(rows):
            for column in range(columns):
                rowOffset = row*tileSize
                columnOffset = column*tileSize
                tiles[tileIndex] = array[slice, rowOffset:rowOffset+tileSize, columnOffset:columnOffset+tileSize].flatten()
                tileIndex += 1
                labels.append(slice)
    return tiles,labels



print("generate X")
# X = randomSlices(mrHead, 70 * 1000, [32,32])
# labels = list(map(str, list(numpy.random.random_integers(0,10,len(z)))))
tileSize = 16
X, labels = sliceTiles(mrHead, tileSize)
# print(X, labels)

tileArray = X.reshape([X.shape[0], tileSize, tileSize])
tileVolume = slicer.util.addVolumeFromArray(tileArray)
tileVolume.SetName("Input Tiles")

print("train on X")
try:
    cvae
except NameError:
    from cvae import cvae
import importlib
importlib.reload(cvae)

embedder = cvae.CompressionVAE(
    X,
    train_valid_split=0.99,
    dim_latent=5,
    #iaf_flow_length=10,
    # cells_encoder=[512, 256, 128],
    #initializer='lecun_normal',
    #batch_size=32,
    #batch_size_test=128,
    #logdir='~/mnist_16d',
    #feature_normalization=False,
    tb_logging=True)
embedder.train(
    learning_rate=1e-4,
    num_steps=int(10e5),
    #dropout_keep_prob=0.6,
    test_every=50,
    lr_scheduling=False)

print("embed X")
z = embedder.embed(X)

#embedder.visualize(z, labels=labels, filename="/tmp/embedding.png")

X_reconstructed = embedder.decode(z)

recontstructedTileArray = X_reconstructed.reshape(tileArray.shape)
recontstructedTileVolume = slicer.util.addVolumeFromArray(recontstructedTileArray)
recontstructedTileVolume.SetName("Reconstructed Tiles")

# not used, but maybe handy some day
def randomSlices(volume, sliceCount, sliceShape):
    layoutManager = slicer.app.layoutManager()
    redWidget = layoutManager.sliceWidget('Red')
    sliceNode = redWidget.mrmlSliceNode()
    sliceNode.SetDimensions(*sliceShape, 1)
    sliceNode.SetFieldOfView(*sliceShape, 1)
    bounds = [0]*6
    volume.GetRASBounds(bounds)
    imageReslice = redWidget.sliceLogic().GetBackgroundLayer().GetReslice()

    sliceSize = sliceShape[0] * sliceShape[1]
    X = numpy.zeros([sliceCount, sliceSize])

    for sliceIndex in range(sliceCount):
        position = numpy.random.rand(3) * 2 - 1
        position = [bounds[0] + bounds[1]-bounds[0] * position[0],
                    bounds[2] + bounds[3]-bounds[2] * position[1],
                    bounds[4] + bounds[5]-bounds[4] * position[2]]
        normal = numpy.random.rand(3) * 2 - 1
        normal = normal / numpy.linalg.norm(normal)
        transverse = numpy.cross(normal, [0,0,1])
        orientation = 0
        sliceNode.SetSliceToRASByNTP( normal[0], normal[1], normal[2], 
                                      transverse[0], transverse[1], transverse[2], 
                                      position[0], position[1], position[2],
                                      orientation) 
        if sliceIndex % 100 == 0:
            slicer.app.processEvents()
        imageReslice.Update()
        imageData = imageReslice.GetOutputDataObject(0)
        array = vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars())
        X[sliceIndex] = array
    return X


