
1. BEI行为事件访谈中一个【行为事件】的关键信息包括：
            - Situation：行为事件的情境或者背景
			- Target：所面临的任务以及目标或者要解决的问题
			- Role：在该事件中的职责或者角色
			- Challenge：完成该目标或者解决该问题，该角色所面临的挑战
			- Thinking：对该事件的思考或者决策
			- Action：面临挑战时所采取的行动举措
			- Result：采取举措后事件的结果
			- Reflection：对整个事件的反思，做得好的，做得不够好的
2. BEI行为事件访谈中所提到的一个【行为事件】是有以下属性的：
	- Match_competency：true or false ,该事件是否能够考察该胜任力，主要根据以下信息来判断，判断的逻辑是，在该任务背景（Situation、Target）下该角色（Role）要克服所面临的挑战（Challenge）是否必须要具备该胜任力，如果是必须要具备，那么值为true
		    - Situation：行为事件的情境或者背景
			- Target：所面临的任务以及目标或者要解决的问题
			- Role：在该事件中的职责或者角色
			- Challenge：完成该目标或者解决该问题，该角色所面临的挑战
	- Detail_sufficient：true or false ，所需要挖掘的信息是否已经完备、充分、具体，如果已经充分，那么值为true，需要挖掘的信息包括：
            - Thinking：对该事件的思考、分析或者决策
			- Action：面临挑战时所采取的行动举措
			- Result：采取举措后事件的结果
			- Reflection：对整个事件的反思，做得好的，做得不够好的
	- Logic_right：true or false ，逻辑上是否合乎情理，可以从以下角度判断，如果以下三条均为true，则该条结论为true，否则为 false，当Logic_right为false时，需要给出理由（Logic_wrong_reason）。分析角度为：
			- 从逻辑上说，采取的举措（Action）是否能够克服挑战（Challenge），结论为true or false 
			- 从逻辑上说，采取的举措（Action）是否能够支撑达成该结果（Result）。结论为true or false 
			- 从逻辑上说，用户面临挑战（Challenge）的思考分析（Thinking）和行动（Action）是一致的，结论为true or false 
3. 提问与追问的流程：
	- Step1-发起提问：从题本中读取胜任力模型和引导提问参考，开始面试后，从题本中选择一个引导提问；
	- step2-确认经历：使用LLM做快速判断，通过候选人的回答来判断候选人是否有问题中所提出的经历，如果候选人表示没有所提出的经历，需要从FBEI题库中在抽取一个不同的问题
	- Step3-行为事件确认：先搜集必要的信息来对 Match_competency坐判断，如果判断为true，则进入Step3，如果不是，重新进入Step1，再次抽取一个问题，该问题与之前抽取的问题不能相同。如果题本中所罗列的可以抽取的问题已经都被抽取了，那么自动结束该胜任力的面试，进入下一个胜任力提问的step1。判断Match_competency所必要的信息为：
							- Situation：行为事件的情境或者背景
							- Target：所面临的任务以及目标或者要解决的问题
							- Role：在该事件中的职责或者角色
							- Challenge：完成该目标或者解决该问题，该角色所面临的挑战
	- Step4-行为事件挖掘：用户已经开始讲述经历或者案例，那么就需要挖掘以下信息，然后进行Detail_sufficient判断，如果为true，则进入下一阶段的判断，如果为false，则继续挖掘未被挖掘到的信息。
				- Thinking：对该事件的思考、分析或者决策
				- Action：面临挑战时所采取的行动举措
				- Result：采取举措后事件的结果
				- Reflection：对整个事件的反思，做得好的，做得不够好的
	 - Step5-Logic_right判断：如果Logic_right为false，则需要基于Logic_wrong_reason进行追问细节信息，直到Logic_right为true；如果Logic_right为true，则可以结束对该胜任力的提问，切换到下一个胜任力，这理论的追问最多3轮。