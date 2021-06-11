# AutoLOD_Blender
Automatic LOD generation &amp; exportation for Blender

Installation : 
- Dowload from relases (https://github.com/Andarael/AutoLOD_Blender/releases)
- In Blender go to Edit>user preferences>addons>install, and select the zip
- Enable the Addon

Usage :
The lod menu is in the scene properties, under "LODs"

To log objects as LOD select them and clic "Set LOD" button
Once the object are LODs, you can use the global buttons to affect all LOD objects instead of only selected ones.

Buttons : 
- Set LOD : log object as LODs, and update them if necessary
- Remove LOD : Remove the LODs from objects
- Apply LOD : Apply the LODs the the mesh data. This is not reversible.


Properties : 
- Agressivity : controlls the LOD generation curve
- Lod Max Level : maximum levels of decimation
- LOD Bias : Increase or decrease LOD level by the Bias amount
- LOD Start Distance : Start generating LODs after this value
- LOD Ration multiplier : Geometry decimation multiplier

Export :
- Select the object to export and clic the export button
- New .obj files will be created in the .blend file current location.
- Lod generation goes from 0 to LOD_MAX_LEVEL
