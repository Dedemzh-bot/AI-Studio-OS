grids.txt中
	Tags参数说明（可以配置多个，分号隔开）
		start:				起点
		blockbox:			阻挡箱子
		box:				箱子
		treasurebox1:		小宝箱
		treasurebox2:		大宝箱
		onlyFront: 			只能正前方互动
		forbidBack: 		禁止背面互动
		disableCollision		禁止碰撞	
		dontInteractAfterMove	前往后立刻互动
		showOutline	是否显示描边
		ShowTipsAfterMoveTo	前往后显示Tips
	
	ClassName参数说明
		rewardbox:			奖励箱子（领取后自动消失）
			奖励id
			领奖后播放的特效
			重置后是否再次刷出（已经领取的情况下）
			
		door:				门
			自动播放开门特效（状态0切换到状态1）
			
		fight:				战斗节点
			战斗id 
		
		itembox:			道具奖励箱（领取后往背包添加一个道具，物件自动消失）
			itemId			道具id 
			itemCount		道具数量，默认1
			
		
		plot:				剧情节点
			剧情id
			
		box_reset:			箱子重置器
			需要重置的箱子id列表
			重置时播放的特效
		
		box_receiver:		箱子接收器
			物件id:			如果不填表示所有物件；如果填了多个，表示其中任意一个满足即可
			特效id:			当上面有目标箱子时播放特效，否则隐藏特效
		
		