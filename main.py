#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import maya.cmds as mc
import maya.mel as mm

class weightRebalance():
	def __init__(self):
		#マックスインフルエンスを指定します
		global MaxInfl
		#四捨五入する桁を設定します
		global roundPoint
		##後でまとめて正規化するので、リストに入れときます
		global skinClusterList
		#エラーを起こしている頂点をリストします
		global errorVertex

		#マックスインフルエンスを指定します
		MaxInfl = 3

		#四捨五入する桁を設定します
		roundPoint = 2

		##後でまとめて正規化するので、リストに入れときます
		skinClusterList = []

		#エラーを起こしている頂点をリストします
		errorVertex = []

	#---------------------------------------------------------------------------------------------------------------------
	def createUI(self, *args):
		if mc.window( 'weightRoundWindow', q=True, ex=True):
			mc.deleteUI( 'weightRoundWindow' )
		mc.window( 'weightRoundWindow' )
		mc.frameLayout( 'mainFrame', p='weightRoundWindow', l='weightRound' )
		mc.rowColumnLayout( 'mainLay', p='mainFrame', nc=2 )
		mc.intField( 'roundWeightFields',p='mainLay', value=3, ann='ex)3-->0.001, 2-->0.01, 1-->0.1' )
		mc.button( 'roundButton', p='mainLay', l='round vtx weight', c= self.roundSkinWeights  )
		mc.intField( 'maxInflFields',p='mainLay', value=3, ann='最大インフルエンス数です。指定することで、頂点ウェイトに対するジョイントの数を減少させます')
		mc.button( 'maxButton', p='mainLay', l='force max influence', c=self.maxInfllenceAdjustment )
		mc.button( 'selectErrorVtxButton', p='mainLay', l='error weight vtx', c= self.thresholdDetermination )
		mc.showWindow( 'weightRoundWindow' )
	#---------------------------------------------------------------------------------------------------------------------
	def weightBalanceList(self, vtx, connectSkinsName, *args):

		#選択した頂点のインフルエンシャルな各ジョイントをリストします
		listWeightJoint = mc.skinPercent( connectSkinsName, vtx, q=True , t=None )
		#リストしたジョイントが支配しているパーセンテージを取得します
		listWeightValue = mc.skinPercent( connectSkinsName, vtx, q=True , v=True )


		#ウェイトをもっているジョイントをピックアップし、ラウンドして格納します
		haveWeightDicBuf = {}
		for i,v in enumerate(listWeightJoint):
			if listWeightValue[i] > 0:
				roundNum = 	round(listWeightValue[i], roundPoint)
				haveWeightDicBuf[v] = roundNum

		return haveWeightDicBuf

	#---------------------------------------------------------------------------------------------------------------------
	def roundSkinWeights(self, *args):
		#マックスインフルエンスを指定します
		global MaxInfl
		MaxInfl = mc.intField( 'roundWeightFields', q=True, value=True )
		#四捨五入する桁を設定します
		global roundPoint
		roundPoint = mc.intField( 'maxInflFields', q=True, value=True )

		##後でまとめて正規化するので、リストに入れときます
		global skinClusterList

		#エラーを起こしている頂点をリストします
		global errorVertex


		#選択した頂点をフラットで取得します。
		selectVert = mc.ls(sl=True,fl=True)

		#プログレスウィンドウ処理
		numberVtx = len(selectVert)
		amount = 0
		mc.progressWindow( title='please weight...', progress=amount, status='now check: 0%', isInterruptable=True )
		#プログレスウィンドウ処理

		for vtx in selectVert:
			#取得した頂点を支配しているスキンクラスターを取得します。
			objSkinName = vtx.split('.')
			connectSkinsName = mm.eval('findRelatedSkinCluster %s' % objSkinName[0])

			#後でまとめて正規化するので、リストに入れときます
			skinClusterList.append(connectSkinsName)

			#スキンクラスタのウェイト値正規化解除
			mc.setAttr (connectSkinsName +".normalizeWeights", 0)

			#選択した頂点のインフルエンシャルな各ジョイントをリストします
			listWeightJoint = mc.skinPercent( connectSkinsName, vtx, q=True , t=None )
			#リストしたジョイントが支配しているパーセンテージを取得します
			listWeightValue = mc.skinPercent( connectSkinsName, vtx, q=True , v=True )


			#ウェイトをもっているジョイントをピックアップし、ラウンドして格納します
			haveWeightDic = {}
			for i,v in enumerate(listWeightJoint):
				if listWeightValue[i] > 0:
					roundNum = 	round(listWeightValue[i], roundPoint)
					haveWeightDic[v] = roundNum


			#ラウンドしたウェイトをすべて足すと、1以外になる場合
			weightPointList = haveWeightDic.values()
			totalPoint = sum(weightPointList)
			if totalPoint != 1:
				print (weightPointList)
				#リスト内の一番大きな値と、それを格納しているリスト番号を取得します
				mx = max(weightPointList)
				mxIndex = weightPointList.index(mx)

				#1から、合計数を引いて、差分を一番大きな値を持つジョイントに足しこんで、それをウェイトリストに再格納します
				diff = 1 - totalPoint
				weightPointList[mxIndex] = mx + diff

				weightedJoints = haveWeightDic.keys()
				for i,v in enumerate(weightedJoints):
					haveWeightDic[v] = weightPointList[i]


			#ウェイトのインフルエンスが規定値を超えている場合はエラーを表示します
			if len(haveWeightDic) > MaxInfl:
				errorVertex.append(vtx)
				print (vtx + u'<---この頂点はマックスイフルエンスが規定値を超えています')


			#結果をウェイト値に戻します
			weightedJoints = haveWeightDic.keys()
			for v in weightedJoints:
				mc.skinPercent( connectSkinsName, vtx, tv=(v, haveWeightDic[v]), normalize=False )


			#プログレスウィンドウ処理
			if mc.progressWindow( q=True, isCancelled=True ):
				break

			adoptNum = str(amount/numberVtx)
			mc.progressWindow( e=True, progress=(int((amount*1.0)/numberVtx*100)), status=('now check:' + adoptNum + '%') )
			amount = amount +1

		mc.progressWindow( endProgress=True )
		#プログレスウィンドウ処理

		#スキンクラスタのウェイト値正規化再設定
		for skinCls in skinClusterList:
			mc.setAttr (skinCls +".normalizeWeights", 1)

		skinClusterList = []
	#---------------------------------------------------------------------------------------------------------------------

	#---------------------------------------------------------------------------------------------------------------------
	def maxInfllenceAdjustment(self, *args):

		#マックスインフルエンスを指定します
		global MaxInfl
		MaxInfl = mc.intField( 'roundWeightFields', q=True, value=True )
		#四捨五入する桁を設定します
		global roundPoint
		roundPoint = mc.intField( 'maxInflFields', q=True, value=True )

		##後でまとめて正規化するので、リストに入れときます
		global skinClusterList

		#エラーを起こしている頂点をリストします
		global errorVertex

		#maxInflenceを超えてウェイトを持っている頂点を調整します
		selectVert = mc.ls(errorVertex,fl=True)

		#プログレスウィンドウ処理
		numberVtx = len(selectVert)
		amount = 0
		mc.progressWindow( title='please weight...', progress=amount, status='now check: 0%', isInterruptable=True )
		#プログレスウィンドウ処理

		for vtx in selectVert:
			#取得した頂点を支配しているスキンクラスターを取得します。
			objSkinName = vtx.split('.')
			connectSkinsName = mm.eval('findRelatedSkinCluster %s' % objSkinName[0])

			#後でまとめて正規化するので、リストに入れときます
			skinClusterList.append(connectSkinsName)

			#スキンクラスタのウェイト値正規化解除
			mc.setAttr (connectSkinsName +".normalizeWeights", 0)

			#ウェイトをもっているジョイントをピックアップし、ラウンドして格納します
			haveWeightDic = self.weightBalanceList(vtx,connectSkinsName)


			#maxInfllenceからどのくらいオーバーしているかをカウントします
			subPoint = len( haveWeightDic ) - MaxInfl

			getMiniPoint = 0.0

			#maxInfllenceを超えてウェイトがなされていた場合、自動調整
			if subPoint > 0:
				#ウェイトの小さい順からソートをかけたリストを作成します
				sortWeightlist = haveWeightDic.items()
				sortWeightlist.sort(key=lambda a: a[1])

				#ジョイントとウェイトのリストを作成します
				jointSortList = []
				pointSortList = []
				for i in sortWeightlist:
					jointSortList.append(i[0])
					pointSortList.append(i[1])

				#小さいウェイトをオーバーしている数分足します
				#オーバーしているインフルエンスを調整するために、小さいウェイトから順番にウェイトを0にしていきます
				for i in range(0,subPoint):
					getMiniPoint = getMiniPoint + pointSortList[i]
					pointSortList[i] = 0

				#平均を計算して、for文でリストを足し算
				avg = round( getMiniPoint / MaxInfl, roundPoint)
				n = -1

				for i in range(0,subPoint):
					pointSortList[n] = round( pointSortList[n] + avg, roundPoint)
					n = n -1


				#合計数が一以外の場合の処理
				total = sum(pointSortList)
				if total != 1:
					sub =  round( 1 - total, roundPoint)
					pointSortList[n] = pointSortList[n] + sub


				#結果をウェイト値に戻します
				for i,v in enumerate(jointSortList):
					mc.skinPercent( connectSkinsName, vtx, tv=(v, pointSortList[i]), normalize=False )

			#プログレスウィンドウ処理
			if mc.progressWindow( q=True, isCancelled=True ):
				break

			adoptNum = str(amount/numberVtx)
			mc.progressWindow( e=True, progress=(int((amount*1.0)/numberVtx*100)), status=('now check:' + adoptNum + '%') )
			amount = amount +1

		mc.progressWindow( endProgress=True )
		#プログレスウィンドウ処理

		#スキンクラスタのウェイト値正規化再設定
		for skinCls in skinClusterList:
			mc.setAttr (skinCls +".normalizeWeights", 1)

	#---------------------------------------------------------------------------------------------------------------------



	#---------------------------------------------------------------------------------------------------------------------
	def thresholdDetermination(self, *args):
		#選択した頂点をフラットで取得します。
		selectVert = mc.ls(sl=True,fl=True)

		#エラーを起こしている頂点を格納します

		errorVertex = []

		numberVtx = len(selectVert)
		amount = 0
		mc.progressWindow( title='please weight...', progress=amount, status='now check: 0%', isInterruptable=True )

		for vtx in selectVert:
			#取得した頂点を支配しているスキンクラスターを取得します。
			objSkinName = vtx.split('.')
			connectSkinsName = mm.eval('findRelatedSkinCluster %s' % objSkinName[0])

			#ウェイトをもっているジョイントをピックアップし、ラウンドして格納します
			haveWeightDic = self.weightBalanceList(vtx,connectSkinsName)

			#ウェイトのインフルエンスが規定値を超えている場合はエラーを表示します
			if len(haveWeightDic) > MaxInfl:
				errorVertex.append(vtx)
				print (vtx + u'<---この頂点はマックスイフルエンスが規定値を超えています'	)


			if mc.progressWindow( q=True, isCancelled=True ):
				break

			adoptNum = str(amount/numberVtx)
			mc.progressWindow( e=True, progress=(int((amount*1.0)/numberVtx*100)), status=('now check:' + adoptNum + '%') )
			amount = amount +1

		mc.progressWindow( endProgress=True )

		if errorVertex != []:
			mc.select(errorVertex,r=True)
			mc.confirmDialog(m='今選択している頂点はマックスインフルエンスをオーバーしています')
		else:
			mc.select(clear=True)
			mc.confirmDialog(m='マックスインフルエンスを越えている頂点は存在しません')


weightRebalance().createUI()
