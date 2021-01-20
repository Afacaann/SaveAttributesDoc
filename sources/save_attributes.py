"""
/***************************************************************************
 SaveAttributes
                                 A QGIS plugin
 This plugin saves the attribute of the selected vector layer as a csv file. 
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-30
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Berk Anbaroğlu
        email                : banbar@hacettepe.edu.tr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

class SaveAttributes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.max_float = sys.float_info.max

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SaveAttributes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Save Attributes')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SaveAttributes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/save_attributes/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Save Attributes'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, 
            "Select output file ",
            "", 
            '*.csv')
        self.dlg.lineEdit.setText(filename)
    
    def input_shp_file(self):
        self.dlg.lineEdit_input_shp.setText("")
        self.dlg.comboBox_id.clear()
        self.shpPath, self._filter = QFileDialog.getOpenFileName(self.dlg, "Select input shp file","", 'ESRI Shapefiles(*.shp *.SHP);; GeoJSON (*.GEOJSON *.geojson);; Geography Markup Language(*.GML)')
        try:
            self.shp = ogr.Open(self.shpPath)
            self.layer = self.shp.GetLayer(0)
            self.name = self.layer.GetName()
        except:
            self.dlg.labelStatus.setText('Status: Wrong Input')
            return
        feature=self.layer[0]
        geometry = feature.GetGeometryRef()
        if (geometry.GetGeometryName()=="POLYGON"):
            self.dlg.labelStatus.setText('Status: Invalid Geometry(Polygon)')
            return
        self.dlg.labelStatus.setText('Status: Ready')
        self.dlg.lineEdit_input_shp.setText(self.shpPath)            
        self.dlg.comboBox_id.clear()
        self.layerDef = self.layer.GetLayerDefn()            
        self.fieldNames = [self.layerDef.GetFieldDefn(i).name for i in range(self.layerDef.GetFieldCount())] 
        self.dlg.comboBox_id.addItems(self.fieldNames)
        
    
    # createShp is supposed to create a new shapefile.
    def createShp(self, input_line, costs, out_shp, sr):
        driver = ogr.GetDriverByName('Esri Shapefile')
        ds = driver.CreateDataSource(out_shp)
        srs = osr.SpatialReference()
        srs.ImportFromProj4(sr)
        layer = ds.CreateLayer('mst', srs, ogr.wkbLineString)
        layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn('cost', ogr.OFTReal))
        defn = layer.GetLayerDefn()
        
        for e,i in enumerate(zip(input_line, costs)):
            feat = ogr.Feature(defn)
            feat.SetField('id', e)
            feat.SetField('cost', i[1])
        
            # Geometry
            feat.SetGeometry(i[0])    
            layer.CreateFeature(feat)
        
        ds = layer = defn = feat = None


    
    def RightTurn(self,p1, p2, p3):
        if (p3[1]-p1[1])*(p2[0]-p1[0]) >= (p2[1]-p1[1])*(p3[0]-p1[0]):
            return False
        return True
            
    def GrahamScan(self,P):
        self.dlg.labelStatus.setText('Status: Graham Scan')
        if len(P)<3:
            return []

        P.sort()			
        L_upper = [P[0], P[1]]		
    
        for i in range(2,len(P)):
            
            self.dlg.progressBar.setValue(int((i/len(P))*100)+1)
            L_upper.append(P[i])
            while len(L_upper) > 2 and not self.RightTurn(L_upper[-1],L_upper[-2],L_upper[-3]):
                del L_upper[-2]
        L_lower = [P[-1], P[-2]]	
        
        for i in range(len(P)-3,-1,-1):
            L_lower.append(P[i])
            while len(L_lower) > 2 and not self.RightTurn(L_lower[-1],L_lower[-2],L_lower[-3]):
                del L_lower[-2]
        del L_lower[0]
        del L_lower[-1]
        L = L_upper + L_lower
        return np.array(L)
    def dist(self,p1, p2): 
        return math.sqrt((p1[0] - p2[0]) * 
                        (p1[0] - p2[0]) +
                        (p1[1] - p2[1]) * 
                        (p1[1] - p2[1])) 

    def bruteForce(self,P): 
        self.dlg.labelStatus.setText('Status: Brute Force Minimum')
        min_val = 0
        point=[]
        n=len(P)
        
        for i in range(n): 
            self.dlg.progressBar.setValue(int((i/len(P))*100)+1)
            for j in range(i + 1, n): 
                if self.dist(P[i], P[j]) > min_val: 
                    min_val = self.dist(P[i], P[j]) 
                    point=[P[i],P[j]]
        return point

    def findPointInLayer(self,layer,P):
        MyPnt=QgsGeometry.fromPointXY(QgsPointXY(P[0],P[1]))      
        feats = layer.getFeatures()
        for feat in feats:
            if MyPnt.intersects(feat.geometry()):
                feature = feat                
                return feat
        return []

    

    def dist(self,p1,p2):
        x1=p1[0]
        y1=p1[1]
        x2=p2[0]
        y2=p2[1]
        return sqrt((x1 - x2) ** 2 + (y1 - y2) **2)

    def closest(self,points_list):
        if len(points_list) < 2:
            return (self.max_float, None, None)  # default value compatible with min function
        return min((self.dist(p1, p2), p1, p2)
                for p1, p2 in combinations(points_list, r=2))

    def closest_between(self,pnt_lst1, pnt_lst2):
        if not pnt_lst1 or not pnt_lst2:
            return (self.max_float, None, None)  # default value compatible with min function
        return min((self.dist(p1, p2), p1, p2)
                for p1, p2 in product(pnt_lst1, pnt_lst2))

    def divide_on_tiles(self,points_list):
        side = int(sqrt(len(points_list)))  # number of tiles on one side of square
        tiles = defaultdict(list)
        min_x = min(x for x, y in points_list)
        max_x = max(x for x, y in points_list)
        min_y = min(x for x, y in points_list)
        max_y = max(x for x, y in points_list)
        tile_x_size = float(max_x - min_x) / side
        tile_y_size = float(max_y - min_y) / side
        for x, y in points_list:
            x_tile = int((x - min_x) / tile_x_size)
            y_tile = int((y - min_y) / tile_y_size)
            tiles[(x_tile, y_tile)].append((x, y))
        return tiles

    def closest_for_tile(self,tiles, tile):
        x_tile=tile[0]
        y_tile=tile[1]
        points = tiles[(x_tile, y_tile)]
        return min(self.closest(points),
                # use dict.get to avoid creating empty tiles
                # we compare current tile only with half of neighbours (right/top),
                # because another half (left/bottom) make it in another iteration by themselves
                self.closest_between(points, tiles.get((x_tile+1, y_tile))),
                self.closest_between(points, tiles.get((x_tile, y_tile+1))),
                self.closest_between(points, tiles.get((x_tile+1, y_tile+1))),
                self.closest_between(points, tiles.get((x_tile-1, y_tile+1))))

    def find_closest_in_tiles(self,tiles):
        return min(self.closest_for_tile(tiles, coord) for coord in tiles.keys())

    def kmean(self,P,classCount,threshold):
        if len(P)==0:
            self.dlg.labelStatus.setText('Status: No Feature Exists')
            return            
        if len(P)<classCount:
            self.dlg.labelStatus.setText('Status: Invalid Class Count')
            return
        if threshold<=0:
            self.dlg.labelStatus.setText('Status: Invalid Threshold')
            return
        self.dlg.labelStatus.setText('Status: KMeans')
        n=len(P)
        classes=[]
        for i in range(classCount):
            x=random.uniform(P[0][0],P[0][0]+1000)
            y=random.uniform(P[0][1],P[0][1]+1000)
            classes.append([x,y])

        
        score=threshold+1000
        while score>threshold:
            QCoreApplication.processEvents()
            
            classPoints=[]
            
            for i in range(classCount):
                classPoints.append([])
            for i in P:
                self.dlg.progressBar.setValue(int((P.index(i)/len(P))*100))
                dists=[]
                for j in classes:
                    dists.append(self.dist(i,j))
                
                classPoints[dists.index(min(dists))].append(i)
            score=0
            for i in range (len(classPoints)):
                xmean=0
                ymean=0
                for j in classPoints[i]:
                    xmean+=j[0]    
                    ymean+=j[1]
                self.dlg.labelStatus.setText('Status: Score='+str(score))
                
                if len(classPoints[i])!=0:
                    score+=self.dist(classes[i],[xmean/len(classPoints[i]),ymean/len(classPoints[i])])
                    classes[i]=[xmean/len(classPoints[i]),ymean/len(classPoints[i])]
                        
            
        return classes,classPoints,score
                    



        
        

    def process(self):

            file_path = self.dlg.lineEdit_input_shp.text()
            if file_path=="":
                self.dlg.labelStatus.setText('Status: Invalid File Name')
                return
            # Open the shp file
            # Second argument tell whether to read (0, default), or to update (1)
            ds = ogr.Open(file_path,0)
            
            if ds is None:
                self.dlg.labelStatus.setText('Status: Invalid File Handle')
                return
                
            # Obtain the layer
            lyr = ds.GetLayer()
            
            # Runs, but does not create a new field-------------
            # lyr.CreateField(ogr.FieldDefn('x', ogr.OFTReal))
            # lyr.CreateField(ogr.FieldDefn('y', ogr.OFTReal))
            # # Runs, but does not create a new field-------------
            
            if (lyr.GetGeomType() == ogr.wkbPoint): #wkb: wll known binary
                type_of_layer = "point"
            elif(lyr.GetGeomType() == ogr.wkbLineString):
                type_of_layer = "line"
                
                   
            vlayer = QgsVectorLayer(self.dlg.lineEdit_input_shp.text(), 
                                    type_of_layer, 
                                    "ogr")
                    
            idFieldName = self.dlg.comboBox_id.currentText()
            useID=not self.dlg.checkBox.isChecked()
            classify=self.dlg.checkClass.isChecked()
            if classify:
                classCount=self.dlg.classCountBox.value()
                threshold=self.dlg.thresholdBox.value()

            # Number of features/records
            num_features = lyr.GetFeatureCount()
            
            
            if not vlayer.isValid():
                print("Layer failed to load!")
            else:
                QgsProject.instance().addMapLayer(vlayer)                
            
            
            vlayer = iface.activeLayer()   
            

            vlayer.startEditing()
            layer_provider = vlayer.dataProvider()
            if(type_of_layer == "point"):
                if ("x" not in [fld.name() for fld in vlayer.fields()]) or ("y" not in [fld.name() for fld in vlayer.fields()]):
                    layer_provider.addAttributes([QgsField('x', QVariant.Double),QgsField('y', QVariant.Double)])
 
            if(type_of_layer == "line"):
                if ("x1" not in [fld.name() for fld in vlayer.fields()]) or ("y1" not in [fld.name() for fld in vlayer.fields()]) or ("x2" not in [fld.name() for fld in vlayer.fields()]) or ("y2" not in [fld.name() for fld in vlayer.fields()]) or ("realLength" not in [fld.name() for fld in vlayer.fields()]) or ("partialLen" not in [fld.name() for fld in vlayer.fields()]) :
                    layer_provider.addAttributes([QgsField('x1', QVariant.Double),QgsField('y1', QVariant.Double),QgsField('x2', QVariant.Double),QgsField('y2', QVariant.Double),QgsField('realLength', QVariant.Double),QgsField('partialLen', QVariant.Double)])
            vlayer.updateFields() 
            vlayer.commitChanges()              
            
            # Iterate over all POIs and add their coordinates to the newly defined fields
            layer = iface.activeLayer()
            layer.startEditing()
            all_features = layer.getFeatures()

            if(type_of_layer == "point"):            

                polyLayer = QgsVectorLayer("Polygon", "temp", "memory")    
                lineLayer = QgsVectorLayer("LineString", "lines", "memory")  
                lineLayer.startEditing()
                if useID:
                    
                    lineLayer.dataProvider().addAttributes([QgsField('id_start', QVariant.Double),QgsField('id_end', QVariant.Double),QgsField('length', QVariant.Double)])
                else:
                    lineLayer.dataProvider().addAttributes([QgsField('length', QVariant.Double)])
                lineLayer.updateFields() 
                lineLayer.commitChanges() 
                #Afacannn's crs code update
                polyLayer.setCrs(vlayer.crs())

                #These are not supported by qgis 3.10
                #crs = polyLayer.crs()
                #crs.createFromId(3857)
                #polyLayer.setCrs(crs)

                #Afacannn's crs code update
                lineLayer.setCrs(vlayer.crs())

                #These are not supported by qgis 3.10
                #crs = lineLayer.crs()
                #crs.createFromId(3857)
                #lineLayer.setCrs(crs)
                P=[]                        
                                        
                for feat in all_features:
                    if feat is None:
                        continue

                    geom = feat.geometry()
                    x = geom.asPoint().x()
                    y = geom.asPoint().y()     
                    P.append([x,y])
                    


                    # X
                    new_x = {feat.fieldNameIndex('x'): x}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_x })                                      
                    # Y
                    new_y = {feat.fieldNameIndex('y'): y}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_y })




                
                
                 


                L=self.GrahamScan(P)
                geoms=[]
                for i in range(0,len(L)):
                    temp=L[i]
                    x=L[i][0]
                    y=L[i][1]
                    geoms.append(QgsPointXY(x,y))
                polygon=QgsGeometry.fromPolygonXY([geoms])
                feature=QgsFeature()
                feature.setGeometry(polygon)            
                polyLayer.dataProvider().addFeatures([feature])
                polyLayer.updateExtents()
                QgsProject.instance().addMapLayer(polyLayer)
                
                

                max_points=self.bruteForce(P)
                first_point=self.findPointInLayer(layer,max_points[0]) 
                last_point=self.findPointInLayer(layer,max_points[1])
                
                geom=first_point.geometry()
                x1=geom.asPoint().x()
                y1=geom.asPoint().y()
                geom1=last_point.geometry()
                x2=geom1.asPoint().x()
                y2=geom1.asPoint().y()
                
                feat = QgsFeature()
                length=self.dist([x1,y1],[x2,y2])
               
                


                feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1,y1),QgsPointXY(x2,y2)]))                
                feat=lineLayer.dataProvider().addFeatures([feat])[1][0]
                lineLayer.startEditing()
                if useID:
                    index=layer.fields().indexFromName(idFieldName)

                    lineLayer.changeAttributeValue(feat.id(),0,first_point.attributes()[int(index)])
                    lineLayer.changeAttributeValue(feat.id(),1,last_point.attributes()[int(index)])
                    lineLayer.changeAttributeValue(feat.id(),2,length)
                else:
                    lineLayer.changeAttributeValue(feat.id(),0,length)                             
                lineLayer.commitChanges()
                lineLayer.updateExtents()






                min_points=self.find_closest_in_tiles(self.divide_on_tiles(P))
                
                first_point=self.findPointInLayer(layer,min_points[1]) 
                last_point=self.findPointInLayer(layer,min_points[2])
                geom=first_point.geometry()
                x1=geom.asPoint().x()
                y1=geom.asPoint().y()
                geom1=last_point.geometry()
                x2=geom1.asPoint().x()
                y2=geom1.asPoint().y()
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x1,y1),QgsPointXY(x2,y2)]))                                
                feat=lineLayer.dataProvider().addFeatures([feat])[1][0]
                length=self.dist([x1,y1],[x2,y2])
                lineLayer.startEditing()
                if useID:
                    index=layer.fields().indexFromName(idFieldName)
                    lineLayer.changeAttributeValue(feat.id(),0,first_point.attributes()[int(index)])
                    lineLayer.changeAttributeValue(feat.id(),1,last_point.attributes()[int(index)])
                    lineLayer.changeAttributeValue(feat.id(),2,length)
                else:
                    lineLayer.changeAttributeValue(feat.id(),0,length)                             
                lineLayer.commitChanges()




                lineLayer.updateExtents()
                QgsProject.instance().addMapLayer(lineLayer)
                if classify:
                    classes,classPoints,score=self.kmean(P,classCount,threshold)

                    polyLayer = QgsVectorLayer("Polygon", "classes", "memory")    
                    polyLayer.setCrs(vlayer.crs())
                    for i in range(len(classes)):                        
                        L=self.GrahamScan(classPoints[i])
                        
                        if len(L)==0:
                            continue
                        geoms=[]
                        for i in range(0,len(L)):
                            
                            temp=L[i]
                            x=L[i][0]
                            y=L[i][1]
                            geoms.append(QgsPointXY(x,y))
                        polygon=QgsGeometry.fromPolygonXY([geoms])
                        feature=QgsFeature()
                        feature.setGeometry(polygon)            
                        polyLayer.dataProvider().addFeatures([feature])
                        polyLayer.updateExtents()

                    QgsProject.instance().addMapLayer(polyLayer)
                    self.dlg.labelStatus.setText('Status: Ready')
                    self.dlg.progressBar.setValue(0)


            if(type_of_layer == "line"):
                for feat in all_features:
                    if feat is None:
                        continue

                    geom = feat.geometry().asMultiPolyline()
                    
                    sum_dist=0

                    for i in geom:
                        for j in range(len(i)-1):
                            p1=i[j]
                            p2=i[j+1]                                                
                            sum_dist+=self.dist([p1.x(),p1.y()],[p2.x(),p2.y()])
                        
                    

                    p1=geom[0][0]
                    p2=geom[-1][-1]
                    
                    x1 = p1.x()
                    
                    y1 = p1.y()
                    
                    x2 = p2.x()
                    
                    y2 = p2.y()
                    

                    
                    new_realLength={feat.fieldNameIndex('realLength'):self.dist([x1,y1],[x2,y2])}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_realLength })      

                       

                    

                    # X1
                    new_x1 = {feat.fieldNameIndex('x1'): x1}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_x1 })                                      
                    # Y1
                    new_y1 = {feat.fieldNameIndex('y1'): y1}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_y1 })    
                    # X2
                    new_x2 = {feat.fieldNameIndex('x2'): x2}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_x2 })                                      
                    # Y2
                    new_y2 = {feat.fieldNameIndex('y2'): y2}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_y2 })

                    new_partialLength={feat.fieldNameIndex('partialLen'):sum_dist}
                    layer.dataProvider().changeAttributeValues({feat.id(): new_partialLength })   
            # Commit changes
            layer.commitChanges()


            self.dlg.labelStatus.setText('Status: Ready')
            self.dlg.progressBar.setValue(0)
            #-------------------------------------------------------------------


    def run(self):
        """Run method that performs all the real work"""
        
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SaveAttributesDialog()
            #self.dlg.pushButton.clicked.connect(self.select_output_file)
            self.dlg.pb_select_layer.clicked.connect(self.input_shp_file)
            self.dlg.okButton.clicked.connect(self.process)
       

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        self.dlg.exec_()
        # See if OK was pressed
        


