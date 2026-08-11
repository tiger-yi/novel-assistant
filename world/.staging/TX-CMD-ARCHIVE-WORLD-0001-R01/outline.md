---
schema: novel-harness/outline/v2
revision: 2
status: frozen
current_arc: ARC-001
world_file: world/outline.md
template_role: init-world
book_title: 拳碎大魏
novel_goal: 重建被世族王室抹去的人间武藏，联合江湖与乡社，以武夫之拳镇住吃人的世族军阀与北狄妖患，终结乱世，让凡人不再卖血求生、人人皆可练武。
volumes:
  - id: ARC-001
    title: 乱世饥荒·血肉为薪
    start_chapter: 1
    end_chapter: 10
    planning_status: frozen
    entry_cause: 大魏末年，北方大饥。流民武夫石横为救病危幼妹石禾卖血被骗，濒死之际唤醒【破限加点】，从此以气血寿元为薪练武，乱世求生。
    goal:
      id: GOAL-ARC-001
      result: 主角从食不果腹的流民成长为击杀里正与乡社豪强的武夫，名动乡里，获边军武威营招揽入伍；幼妹暂得活路。
      completion_conditions:
        - 石横击杀里正周满山与乡社豪强，清算卖血骗局。
        - 石横从皮肉力进入筋骨阶，掌握一门成体系拳术。
        - 石横守住村落战乱首波，名声传至边军斥候。
        - 武威营招揽文书送达，石横托付乡邻并携妹入伍。
      required_causality:
        - 卖血骗局与粮链世族、血铺、里正构成的上游证据链被逐步揭开。
        - 每次加点以气血寿元为代价，胜利伴随伤亡与仇怨。
        - 幼妹石禾之病被认定为"命被人抽走"，指向世族血田线索，作为跨卷旧账保留。
      forbidden_outcomes:
        - 首卷灭绝粮链世族或清除其幕后力量（须留作后续卷旧账）。
        - 加点不付代价或凭面板无代价速成。
        - 主角无量级引入妖域、京城或诸郡势力。
      completion_evidence: 卷终正文、章节摘要及 characters/timeline/hooks 实体证据。
    milestones:
      - id: MS-ARC-001-01
        due_chapter: 3
        outcome: 觉醒【破限加点】，一拳打穿恶霸侯三、逼退里正，立"镇不平自己上"目标。
      - id: MS-ARC-001-02
        due_chapter: 6
        outcome: 顶住第一波饥民暴乱与流寇洗村，一战成名，获边军斥候赵却注意。
      - id: MS-ARC-001-03
        due_chapter: 10
        outcome: 追查走私粮链，反杀雇凶主使乡社豪强，武威营招揽文书入村，携妹入伍。
    chapters:
      - id: CH-0001
        task: 饥寒卖血被骗，幼妹咳血等死；濒死之际面板半激活，点明生存主目标。
        preconditions:
          - 大魏末年北方大饥，村落断粮断药。
          - 幼妹石禾病重，需要药材与粮食。
        conflict: 血铺掌柜麻六压价诈血，回家无粮无药，石横濒死。
        outcome: 石横寿元被抽、濒死，破限加点面板以"气血/寿元为薪"半激活，获得第一次刻意晋升机会。
        arc_contribution: 建立生存恐惧主驱动力与加点成本机制。
        closing_pull: 面板浮现"破限"提示，暗示肉体极限可突破。
        milestone: MS-ARC-001-01
        golden_three_role: inciting
        status: published
      - id: CH-0002
        task: 第一次加点，气血入体的具象变化，明确面板规则与代价。
        preconditions:
          - 石横从卖血濒死状态苏醒，面板可用。
        conflict: 是否拿命赌命；村中一名病儿偷走半碗粮，考验石横取舍。
        outcome: 石横完成第一次加点，皮肉力初成、能徒手打碎柴木，温饱暂时解决。
        arc_contribution: 金手指第一课，确立"消耗可见、勤战才能补血"的规则。
        closing_pull: 里正周满山带恶霸侯三上门，冲突一触即发。
        milestone: MS-ARC-001-01
        golden_three_role: feedback
        status: published
      - id: CH-0003
        task: 一拳打穿恶霸侯三、逼退里正，名动乡里，确立守护目标。
        preconditions:
          - 石横皮肉力初成。
          - 里正带恶霸上门强索血钱并意欲夺妹。
        conflict: 恶霸持刀相逼，围观村人不敢相帮。
        outcome: 石横一拳打穿侯三，震慑里正；村人暗中改观，石横立下"镇不平自己上"的誓言。
        arc_contribution: 卷目标核心——从被压迫者变为能自持武力的守护者。
        closing_pull: 里正放出"买粮链"狠话，暗示背后有人在操控饥荒。
        milestone: MS-ARC-001-01
        golden_three_role: goal-lock
        status: published
      - id: CH-0004
        task: 偷师村中拳脚、攒药医妹，识破里正爪牙构陷。
        preconditions:
          - 石横立足村落，急需系统武艺与药材。
        conflict: 药铺掌柜被里正爪牙收买拒卖并构陷石横；村人劝其忍让。
        outcome: 石横借流民拳谱习得入门拳路，识破布局保住石禾用药，战力进入稳定上升期。
        arc_contribution: 完成第一次资源博弈，强化"被人吃"到"不吃亏"的转变。
        closing_pull: 流寇哨探在村外出现，村中人心浮动。
        milestone: MS-ARC-001-02
        status: published
      - id: CH-0005
        task: 组织乡邻设防、击退第一波流寇先锋。
        preconditions:
          - 流寇哨探确认，大股遭灾流民将行洗掠。
        conflict: 村中人心涣散、农具难敌刀兵，里正又添乱。
        outcome: 石横以武压服离心者，率乡邻守住村口、歼灭流寇先锋，夺回口粮。
        arc_contribution: 角色从"护亲"升维到"护乡"，为名动乡里铺路。
        closing_pull: 远处尘土再起，更大的流寇股压境而来。
        milestone: MS-ARC-001-02
        status: published
      - id: CH-0006
        task: 血战大股流寇，一战成名，获边军斥候赵却现身。
        preconditions:
          - 大股流寇围攻村落。
        conflict: 敌众我寡、乡邻伤亡，石横必须独自断后。
        outcome: 石横以命换命守住村落、击溃流寇主力，重伤养息，名声传至过境边军斥候。
        arc_contribution: 完成 MS-ARC-001-02，从流民武者成为一方小有名气之人。
        closing_pull: 斥候赵却抛出武威营招揽意向，并暗示乱世只有边军能保活命。
        milestone: MS-ARC-001-02
        status: published
      - id: CH-0007
        task: 反向追查血铺骗局上游，挖出走私粮链。
        preconditions:
          - 石横伤愈，掌握里正与血铺勾结证据。
        conflict: 粮商买手齐管事闻讯灭口，里正欲借乡里公审反制。
        outcome: 石横破解灭口局，从齐管事口中追出走私粮链，锁定幕后"京中世族"字眼。
        arc_contribution: 把首卷私怨升级为跨卷征途的引线，旧账开始累积。
        closing_pull: 石禾之病被老医师道出："这孩子的命，像是被人抽走了一样。"
        milestone: MS-ARC-001-03
        status: published
      - id: CH-0008
        task: 与乡社豪强周旋救妹，破真假药师局，稳固乡望。
        preconditions:
          - 石禾病危，被指与"命被抽走"有关。
          - 乡社豪强盯上石横，施压换命换药。
        conflict: 豪强以石禾要挟，设真假药师陷阱。
        outcome: 石横识破圈套，以武力与智谋保住石禾，乡望进一步稳固。
        arc_contribution: 强化"守护"的人性锚点，并坐实世族血田线索。
        closing_pull: 豪强放言雇凶，石横预判反扑并主动布防。
        milestone: MS-ARC-001-03
        status: published
      - id: CH-0009
        task: 反杀雇凶主使乡社豪强，清算里正与血铺，完成今卷仇怨闭环。
        preconditions:
          - 豪强雇凶反扑已启动。
          - 武威营招揽文书将至。
        conflict: 主使联手足处江湖的刺客，村人再度观望，石横必须独挑强敌。
        outcome: 石横击杀雇凶主使与刺客，里正与血铺掌柜伏诛，卖血骗局在今卷层面清算。
        arc_contribution: 完成 MS-ARC-001-03 主链，实现"镇不平自己上"的复仇闭环。
        closing_pull: 账本残页上露出"京中世族"与"武威营"两条线的交集。
        milestone: MS-ARC-001-03
        status: published
      - id: CH-0010
        task: 托付乡邻、携妹入伍离乡，完成卷目标并布下跨卷旧账。
        preconditions:
          - 武威营招揽文书送达。
          - 石禾病情稳定，需长期供奉药材。
        conflict: 离乡抉择；赴边意味着被消耗，却又是乡邻与幼妹唯一活路。
        outcome: 石横托付乡邻守护、携妹赴威营入伍，卷目标达成；京中世族与妖患情报收于卷末。
        arc_contribution: 完成卷终态——国家机器"吃人"本质第一次向主角展开。
        closing_pull: 北狄铁骑南侵与妖潮情报终幕，为卷二边军篇立起更大的风浪。
        milestone: MS-ARC-001-03
        status: published
  - id: ARC-002
    title: 边军武威营·妖潮初镇
    start_chapter: 11
    end_chapter: 120
    planning_status: frozen
    entry_cause: 石横携妹进入边军武威营，在军功派与士族空降兵之间周旋，首次直面北狄铁骑与妖患潮；沿商道与军驿，世族的税令、禁武告示与通缉悬赏已在边关低层流传，为后续渗透埋下生活化种子。
    goal:
      id: GOAL-ARC-002
      result: 石横在武威营立身、首镇妖潮，勘破"武夫为消耗品"的军中真相，并积累入京动机。
      completion_conditions:
        - 石横在武威营站稳脚跟，获军功派赏识。
        - 首镇妖潮并结识关键袍泽与女主线人物。
        - 勘破军中粮商掮客吸血的消耗政策，埋下反制。
      required_causality:
        - 军中消耗政策与京中世族粮链为同一条吸血链。
        - 世族先以税令、禁武告示、通缉悬赏与粮价传闻渗入边关日常，再于卷三由粮道冲突正面登场。
        - 北狄铁骑、妖患潮与军功派/士族空降的矛盾贯穿全卷。
      forbidden_outcomes:
        - 石横在本卷即推翻边军或清除世族。
        - 妖潮解决后妖线完全消失。
      completion_evidence: 卷终正文、章节摘要及相关实体证据。
    milestones:
      - id: MS-ARC-002-01
        due_chapter: 20
        outcome: 石横在武威营站稳脚跟，获军功派赏识，初历边关哨战立首功。
      - id: MS-ARC-002-02
        due_chapter: 40
        outcome: 初历北狄战事立军功，结识关键袍泽、女主线深化，士族空降矛盾全面显露。
      - id: MS-ARC-002-03
        due_chapter: 80
        outcome: 首镇妖潮、大破妖患，勘破军中粮商掮客吸血与"武夫为消耗品"真相一角。
      - id: MS-ARC-002-04
        due_chapter: 120
        outcome: 妖患暂定，消耗政策证据集齐并埋下反制，携军功与妖患情报入京，卷目标达成。
    chapters:
      - id: CH-0011
        task: 入伍首日，窥见军饷克扣与消耗本质，安顿石禾。
        preconditions:
          - 石横携妹入营授卒籍。
          - 北狄/妖潮双压临前。
        conflict: 新卒与老兵规矩碰撞，军饷一层层剥落。
        outcome: 石横安顿石禾，初识营中吸血账，立"活着+记账"目标。
        arc_contribution: 卷二开场，国家机器吃人从营规层面展开。
        closing_pull: 首日军务操演点名。
        milestone: MS-ARC-002-01
        golden_three_role: inciting
        status: planned
      - id: CH-0012
        task: 首次操演，战阵拳实战验证。
        preconditions:
          - 石横入籍，筋骨阶初成。
        conflict: 操演中以新卒身份被压，拳路受老兵质疑。
        outcome: 石横以拆招加蛮力打服同伍，军功派伍长留意。
        arc_contribution: 战阵拳立足，战力可信。
        closing_pull: 士族空降校尉点名石横。
        milestone: MS-ARC-002-01
        golden_three_role: feedback
        status: planned
      - id: CH-0013
        task: 顶回士族空降校尉克扣，立营中"镇不平"目标。
        preconditions:
          - 士族校尉借新卒立威。
        conflict: 校尉克扣军饷逼石横低头。
        outcome: 石横以军规顶回，结怨士族、获军功派青眼，锁定卷目标。
        arc_contribution: 卷目标锁定：军中不公亦须镇不平。
        closing_pull: 军功派老卒暗示"营里的账更深"。
        milestone: MS-ARC-002-01
        golden_three_role: goal-lock
        status: planned
      - id: CH-0014
        task: 打探营中粮账，撞见粮商掮客接头苗头。
        preconditions:
          - 石横立足，开始留心营务。
        conflict: 军需官与掮客接头被石横撞见一角。
        outcome: 石横记下掮客面孔与粮账异常，与怀里残账隐隐对应。
        arc_contribution: 消耗政策线索起步，SEED-0001 卷二推进。
        closing_pull: 掮客警觉回头。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0015
        task: 石禾病势反复，温白边关寻药遇阻，石横接军务换药资。
        preconditions:
          - 边关药贵、军属月粮薄。
        conflict: 药资不足、军中克扣挤压。
        outcome: 温白行医搭药，石禾病势稳住，石横记下药价账。
        arc_contribution: 女主线延续，资源压力具体化。
        closing_pull: 温白查得北疆田庄抽命线索。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0016
        task: 赵却引见军功派老将，过拳关获操演机会。
        preconditions:
          - 石横新卒小有名气。
        conflict: 老将试拳，士族掣肘。
        outcome: 石横过拳关，获军功派正式认可。
        arc_contribution: 军功派赏识积累。
        closing_pull: 操演对阵士族空降兵安排已定。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0017
        task: 操演小比胜士族空降兵。
        preconditions:
          - 石横获操演资格。
        conflict: 空降兵有后台、石横无靠山。
        outcome: 石横凭硬实力取胜，当场结怨。
        arc_contribution: 战功路径首现，士族矛盾升级。
        closing_pull: 校尉撂话"走着瞧"。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0018
        task: 士族校尉报复，石横以军规周旋。
        preconditions:
          - 石横结怨士族。
        conflict: 苦差累伤、军饷再扣。
        outcome: 石横借军规与军功派调解化解，反记一笔账。
        arc_contribution: 周旋能力成长，消耗真相渐进。
        closing_pull: 北狄哨骑犯境警报。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0019
        task: 随斥候小队出哨，初历北狄哨骑。
        preconditions:
          - 边关警讯起。
        conflict: 步卒对骑、雪地伏击。
        outcome: 石横以地形加蛮力掩护小队退敌，赵却另眼相看。
        arc_contribution: 首次北狄接触，边关战事开场。
        closing_pull: 哨骑背后大队集结痕迹。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0020
        task: 哨探小胜归营论功，军功派正式接纳。
        preconditions:
          - 斥候立功归来。
        conflict: 军功分配被士族分润。
        outcome: 石横获首笔军功，军功派正式接纳，完成 MS-ARC-002-01。
        arc_contribution: 卷目标条件一（站稳脚跟获赏识）达成。
        closing_pull: 北狄袭扰掠边村消息传来。
        milestone: MS-ARC-002-01
        status: planned
      - id: CH-0021
        task: 北狄掠边村，石横随队救援。
        preconditions:
          - 北狄袭扰边村。
        conflict: 骑掠如风、边民四散。
        outcome: 石横率小队撕开包围，救回边民。
        arc_contribution: 战阵拳实战化，护民之名初立。
        closing_pull: 被掠边民口中北狄营帐规模。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0022
        task: 步对骑吃亏，悟战阵配合。
        preconditions:
          - 石横小胜后轻敌。
        conflict: 北狄骑军合围，石横孤勇吃亏。
        outcome: 石横以袍泽死伤为代价悟出"拳入战阵"门道。
        arc_contribution: 从单打独斗到战阵思维。
        closing_pull: 军功派老卒负伤。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0023
        task: 守边村战，石横再立护民功。
        preconditions:
          - 边村再遭侵扰。
        conflict: 敌众我寡、民怨军疲。
        outcome: 石横组织边民协防，守村成功，获"护民"之名。
        arc_contribution: 护乡升维护民，名望扩大。
        closing_pull: 士族校尉欲把军功记到自己名下。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0024
        task: 军功分配不公，石横据理力争。
        preconditions:
          - 士族空降兵强占军功。
        conflict: 石横战功被侵夺，军功派与士族对簿。
        outcome: 石横以军规与证人夺回功名，士族矛盾激化。
        arc_contribution: 军中公平之争，消耗政策暗影。
        closing_pull: 温白告知田庄线索。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0025
        task: 温白边村行医，发现北疆田庄抽命线索。
        preconditions:
          - 温白随军行医。
        conflict: 抽命手法与北疆世族田庄勾连。
        outcome: 温白记下田庄取人命的证据链。
        arc_contribution: SEED-0002 推进，血田线索北上。
        closing_pull: 田庄爪牙盯上温白。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0026
        task: 石横护温白查证，初遇田庄爪牙。
        preconditions:
          - 温白欲入田庄查证。
        conflict: 田庄以官势压人，爪牙持械。
        outcome: 石横以军卒身份镇住场子，护温白脱身。
        arc_contribution: 女主线深化，血田线索具象。
        closing_pull: 爪牙报信"京里那位"。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0027
        task: 与田庄周旋，温白取回关键证据。
        preconditions:
          - 田庄戒备，证据难取。
        conflict: 庄内庄外两线周旋。
        outcome: 石横声东击西，温白取回一页取人名单。
        arc_contribution: 血田证据再添一环。
        closing_pull: 名单上出现云乡旧识的名字。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0028
        task: 小股兽妖扰边，边军初触妖患。
        preconditions:
          - 妖潮迹象抬头。
        conflict: 兽妖皮糙肉厚，寻常刀兵难破。
        outcome: 边军以劲弩火攻退妖，石横见识妖物弱点。
        arc_contribution: 妖患线进入卷二主舞台。
        closing_pull: 猎队传信妖群集结。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0029
        task: 石横对妖初战，识妖丹价值。
        preconditions:
          - 妖物散患犯境。
        conflict: 妖力凶悍，石横肉身硬撼。
        outcome: 石横以筋骨阶硬功搏杀兽妖，首获妖丹。
        arc_contribution: 妖丹战利品与杀伐偿还机制展开。
        closing_pull: 军需官对妖丹开价。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0030
        task: 军功派提出"以武夫耗妖"策略，石横警惕。
        preconditions:
          - 妖患渐重，边军求策。
        conflict: 填人耗妖的消耗逻辑浮出台面。
        outcome: 石横识破策略背后的消耗本质，心生警惕。
        arc_contribution: 消耗政策露头，武夫即消耗品伏笔。
        closing_pull: 士族校尉附和并要军功提成。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0031
        task: 石横杀伐练拳，筋骨阶巩固。
        preconditions:
          - 连战积累，气血渐旺。
        conflict: 练拳过猛，换骨旧患复发。
        outcome: 石横完成筋骨阶巩固，一拳碎石墙。
        arc_contribution: 战力成长有据，代价可见。
        closing_pull: 同伍袍泽被征入"耗妖队"。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0032
        task: 袍泽情谊深化，结识关键同袍。
        preconditions:
          - 石横军中立足。
        conflict: 袍泽各有苦楚与旧账。
        outcome: 石横与老卒、同伍结下生死交情。
        arc_contribution: 军功派袍泽线铺开。
        closing_pull: 老卒提及早年"填妖口"的兄弟。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0033
        task: 士族空降与军功派粮饷案爆发。
        preconditions:
          - 军饷克扣积怨已深。
        conflict: 粮饷案两派互相攻讦。
        outcome: 石横以人证稳住军心，案情暂压。
        arc_contribution: 军中矛盾结构全面显现。
        closing_pull: 掮客影子再现于军需库。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0034
        task: 石横卷入冲突调解，两边周旋。
        preconditions:
          - 两派剑拔弩张。
        conflict: 站队即错，不站亦难。
        outcome: 石横以"兵要吃饭"压住局面，两头留余地。
        arc_contribution: 不站队立身之道确立。
        closing_pull: 士族校尉单独召见。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0035
        task: 粮商掮客介入军中，军饷克扣坐实。
        preconditions:
          - 掮客渗透军需。
        conflict: 掮客抬价压饷，兵士哗然。
        outcome: 石横暗查坐实掮客吸血链。
        arc_contribution: 军中粮商掮客吸血主线确立。
        closing_pull: 掮客背后的印信像"京中世族"。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0036
        task: 北狄增兵，边关战云密布。
        preconditions:
          - 北狄大队集结。
        conflict: 边军兵力粮秣吃紧。
        outcome: 石横随队加固防务，备战。
        arc_contribution: 北狄线压力抬升。
        closing_pull: 斥候急报北狄先锋将至。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0037
        task: 斥候情报战，石横随赵却深入北境。
        preconditions:
          - 北狄布防不明。
        conflict: 敌境情报风险极高。
        outcome: 石横以拳开路护赵却取回布防图。
        arc_contribution: 情报线展开，斥候信任加深。
        closing_pull: 布防图一角露出妖物烙印。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0038
        task: 北狄小规模进犯，边军迎战。
        preconditions:
          - 北狄先锋犯境。
        conflict: 骑阵冲锋、步卒相持。
        outcome: 石横随军顶住先锋，双方各有伤亡。
        arc_contribution: 边军首战，战阵拳实战检验。
        closing_pull: 妖物随北狄军阵出现。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0039
        task: 石横阵前立功，破敌斩获。
        preconditions:
          - 两军对峙相持。
        conflict: 北狄铁骑冲阵，石横所在阵脚将溃。
        outcome: 石横以血肉之躯稳住阵线，斩敌首级。
        arc_contribution: 首份实打实军功。
        closing_pull: 妖物混入溃兵袭击伤兵。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0040
        task: 战后论功，军功派赏识与士族压制并存。
        preconditions:
          - 边关战事暂歇。
        conflict: 军功分配、妖患后患两线挤压。
        outcome: 石横获军功派重赏，同时被士族记名，完成 MS-ARC-002-02。
        arc_contribution: 卷目标条件二前半达成，双线张力立起。
        closing_pull: 妖潮集结情报坐实，边关面临大考。
        milestone: MS-ARC-002-02
        status: planned
      - id: CH-0041
        task: 妖潮渐起，边关戒严。
        preconditions:
          - 妖群集结，前哨村空。
        conflict: 防务吃紧、人心浮动。
        outcome: 石横随军转入妖患防线。
        arc_contribution: 妖潮主线进入主舞台。
        closing_pull: 妖潮前锋夜袭前哨。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0042
        task: 妖丹经济展开，猎妖队与行情入眼。
        preconditions:
          - 妖患越重，妖丹越贵。
        conflict: 妖丹被军方与掮客垄断。
        outcome: 石横看清妖丹流通与吸血链关系。
        arc_contribution: 资源经济与社会运行展开。
        closing_pull: 猎妖行会信使入营。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0043
        task: 石横参与猎妖，首获妖丹。
        preconditions:
          - 石横入猎妖队。
        conflict: 妖物凶悍、猎队各怀心思。
        outcome: 石横猎得兽妖，妖丹入袋，战力有望再进。
        arc_contribution: 杀伐偿还与妖丹炼化路径落地。
        closing_pull: 掮客登门要收妖丹。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0044
        task: 妖潮先锋犯边，小规模妖战。
        preconditions:
          - 妖潮前锋逼营。
        conflict: 妖群悍不畏死、伤亡惨重。
        outcome: 石横随军击退先锋，但伤亡换防。
        arc_contribution: 妖战代价具象化。
        closing_pull: 阵亡名单被军需官"记账"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0045
        task: 杀伐偿还炼化妖丹，战力提升。
        preconditions:
          - 石横斩妖有功。
        conflict: 炼化妖丹与寿元代价并存。
        outcome: 石横以妖丹补气血，战力再进一档。
        arc_contribution: 战力成长符合破限规则。
        closing_pull: 妖丹账目与军饷账并作一处。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0046
        task: 妖患消耗之策暴露，武夫填妖口。
        preconditions:
          - 妖患日重，边军兵力吃紧。
        conflict: 上层以武夫为耗材的簿子被石横撞见。
        outcome: 石横确认"武夫即消耗品"的真相一角。
        arc_contribution: 卷目标核心真相推进。
        closing_pull: 老卒被点名入耗妖队。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0047
        task: 温白查明抽命线索指北疆田庄，石横埋入京查账动机。
        preconditions:
          - 温白追查抽命源头。
        conflict: 田庄血田与军中消耗同链渐明。
        outcome: 石横将血田与军账并案，立"入京查账"动机。
        arc_contribution: 抽命线与军中线合流。
        closing_pull: 田庄名号与残账印文同出一源。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0048
        task: 士族校尉勾结掮客挪用军粮。
        preconditions:
          - 妖患围城，军粮吃紧。
        conflict: 军粮被挪、前线挨饿。
        outcome: 石横查获挪用证据，隐忍不发作。
        arc_contribution: 掮客-士族勾结坐实。
        closing_pull: 证据被掮客察觉。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0049
        task: 石横暗查粮账，与怀里残账对应。
        preconditions:
          - 石横握挪用线索。
        conflict: 军需账目与残账印文吻合。
        outcome: 石横确认军中粮账即京中世族粮道一脉。
        arc_contribution: SEED-0001 卷二大推进。
        closing_pull: 掮客欲灭口账房。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0050
        task: 妖潮主力逼近，边军备战。
        preconditions:
          - 妖潮主力云集。
        conflict: 兵力不足、妖潮势大。
        outcome: 石横参与布防，献上地形战法。
        arc_contribution: 妖潮决战前奏。
        closing_pull: 妖潮前锋夜探营栅。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0051
        task: 妖潮前哨战，袍泽伤亡，石横悲愤。
        preconditions:
          - 妖潮先锋犯营。
        conflict: 袍泽战死、妖势不退。
        outcome: 石横率队死守，以伤换退，痛失同袍。
        arc_contribution: 战争代价与情感锚点。
        closing_pull: 阵亡同袍的军饷仍被克扣。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0052
        task: 石横献策借地形火攻，军功派采纳。
        preconditions:
          - 妖潮前锋被阻。
        conflict: 正面硬拼伤亡过大。
        outcome: 石横以地形火攻破妖潮一路，获军功派信重。
        arc_contribution: 以智补力，妖战破局。
        closing_pull: 妖潮主力调整攻向。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0053
        task: 小胜妖潮先锋，石横声望起。
        preconditions:
          - 火攻奏效。
        conflict: 追击败局中士族抢功。
        outcome: 石横稳守战果，兵士传其名。
        arc_contribution: 声望积累。
        closing_pull: 妖丹战利分配之争。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0054
        task: 士族空降兵怯战争功，石横周旋。
        preconditions:
          - 士族兵观战抢功。
        conflict: 怯战者分功，奋死者无赏。
        outcome: 石横以战报实情压回士族冒功。
        arc_contribution: 军中不公持续对抗。
        closing_pull: 校尉调石横入险地。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0055
        task: 妖丹分配冲突，掮客吸血坐实。
        preconditions:
          - 妖丹战利丰厚。
        conflict: 掮客压价收丹、兵士白忙。
        outcome: 石横当众点破掮客盘剥，树敌。
        arc_contribution: 掮客吸血链具象。
        closing_pull: 掮客背后的军需官出面。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0056
        task: 石横温白战场协作，情愫加深。
        preconditions:
          - 妖战伤兵众多。
        conflict: 石横负伤，温白救伤。
        outcome: 战场生死间两人情愫落定。
        arc_contribution: 女主线正式推进。
        closing_pull: 温白透露血田与军中同源。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0057
        task: 老卒重伤临终点破"武夫是消耗品"。
        preconditions:
          - 老卒被耗妖队拖垮。
        conflict: 老卒弥留，真相将随他入土。
        outcome: 老卒临终托账，石横接过旧账。
        arc_contribution: 卷目标核心真相由袍泽之死坐实。
        closing_pull: 老卒口中的"京里人"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0058
        task: 石横立誓查清军中吸血账。
        preconditions:
          - 老卒之死刺激。
        conflict: 敌我之外还有账要算。
        outcome: 石横以老卒遗愿立誓，暗账加厚。
        arc_contribution: 消耗政策主线决心确立。
        closing_pull: 妖潮第二次大攻将至。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0059
        task: 妖潮第一次大攻，边军苦战。
        preconditions:
          - 妖潮倾巢来攻。
        conflict: 营栅将破、伤亡遍地。
        outcome: 石横血战稳线，边军顶住首波。
        arc_contribution: 妖潮决战蓄力。
        closing_pull: 妖王虚影于潮后显现。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0060
        task: 石横阵前立功，获伍长职。
        preconditions:
          - 守营立功。
        conflict: 士族欲压其晋升。
        outcome: 石横凭战功升任伍长。
        arc_contribution: 军功晋升路径。
        closing_pull: 伍长带队首务是"耗妖队轮值"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0061
        task: 战后清账，消耗真相血淋淋展开。
        preconditions:
          - 妖潮暂退。
        conflict: 妖丹、尸体、伤亡各有账。
        outcome: 石横看清武夫性命如何被折成军需。
        arc_contribution: 消耗政策全貌一角。
        closing_pull: 阵亡抚恤被掮客吞没。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0062
        task: 石横开始暗记军中账。
        preconditions:
          - 石横掌伍长之权。
        conflict: 记账引火烧身。
        outcome: 石横以老兵旧册为底，暗记军饷妖丹伤亡。
        arc_contribution: 反制准备起步。
        closing_pull: 账册被人翻动痕迹。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0063
        task: 北狄借妖潮动作，双压交汇。
        preconditions:
          - 妖患拖住边军。
        conflict: 北狄趁势袭边。
        outcome: 石横两线救火，心力交瘁。
        arc_contribution: 北狄妖潮双压困境坐实。
        closing_pull: 军报暗示"上面有人通狄"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0064
        task: 军功派与士族矛盾在妖潮下升级。
        preconditions:
          - 双压之下军心浮。
        conflict: 两派互指通敌。
        outcome: 石横稳住本伍，暂压内斗。
        arc_contribution: 军中结构矛盾深化。
        closing_pull: 士族校尉连夜密会掮客。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0065
        task: 战时粮道被掮客垄断，边军粮荒。
        preconditions:
          - 妖战绵延、粮道受阻。
        conflict: 掮客囤粮抬价，兵士断粮。
        outcome: 石横率伍开荒猎妖换粮自救。
        arc_contribution: 粮道-消耗链在经济面坐实。
        closing_pull: 温白以药易粮解燃眉。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0066
        task: 石横设法弄粮，猎妖换粮落地。
        preconditions:
          - 军粮断供。
        conflict: 掮客垄断、妖患遍地。
        outcome: 石横以妖丹走猎妖行会换粮，自救成功。
        arc_contribution: 妖丹经济与自保路径。
        closing_pull: 行会信使带来京中粮价消息。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0067
        task: 温白救妖伤边民，妖丹入药。
        preconditions:
          - 妖气伤人难治。
        conflict: 药路不通、妖毒难解。
        outcome: 温白以妖丹配药救回边民。
        arc_contribution: 妖丹入药用，社会运行细节。
        closing_pull: 妖丹药效惊动掮客。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0068
        task: 妖丹加杀伐，石横向气血境过渡。
        preconditions:
          - 连斩妖物积累。
        conflict: 换骨向聚血过渡，代价加重。
        outcome: 石横战力气血渐盛，筋骨阶圆满。
        arc_contribution: 战力成长与代价同步。
        closing_pull: 妖潮第二波逼近。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0069
        task: 妖潮第二波，更大规模。
        preconditions:
          - 妖潮复聚。
        conflict: 妖势更猛、边军疲敝。
        outcome: 石横率伍死守，再次顶住。
        arc_contribution: 妖潮决战梯度抬升。
        closing_pull: 妖王亲征迹象。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0070
        task: 石横率队守要害，成名边关。
        preconditions:
          - 妖潮第二波围要害。
        conflict: 孤悬之险、退无可退。
        outcome: 石横以地形拳法血战成名，兵士景从。
        arc_contribution: 声望与号召力成型。
        closing_pull: 士族借机把石横抬上"耗妖队"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0071
        task: 凝聚袍泽士气，共御妖患。
        preconditions:
          - 连战疲惫。
        conflict: 兵无战心、士气将崩。
        outcome: 石横以"镇不平"聚拢人心，士气复振。
        arc_contribution: 主角精神感召力。
        closing_pull: 妖潮围困边村。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0072
        task: 妖潮围边村，石横救援。
        preconditions:
          - 边村被妖围困。
        conflict: 妖群封路、救人如救火。
        outcome: 石横率队撕开妖围，救出边民。
        arc_contribution: 护民主线延续。
        closing_pull: 被救边民指向"血田"。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0073
        task: 接触猎妖行会，妖丹交易与情报网。
        preconditions:
          - 石横有妖丹货源。
        conflict: 行会与军方利益纠缠。
        outcome: 石横与行会建立交易与情报合作。
        arc_contribution: 猎妖行会（FAC-0005）前置登场。
        closing_pull: 行会透露妖潮来源非天然。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0074
        task: 掮客与世族妖丹走私证据外泄。
        preconditions:
          - 妖丹行情走高。
        conflict: 走私与军需争利。
        outcome: 石横截获走私凭证，握世族铁证。
        arc_contribution: 世族-掮客-军需铁证成型。
        closing_pull: 掮客灭口内线。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0075
        task: 石横握证据隐而不发。
        preconditions:
          - 石横持走私凭证。
        conflict: 发作则军心动荡，不发则养痈。
        outcome: 石横将证据留作后卷把柄。
        arc_contribution: 证据链积累，入京引子。
        closing_pull: 妖潮决战前夕。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0076
        task: 妖潮决战前夜，军功派密议。
        preconditions:
          - 妖潮决战在即。
        conflict: 战与守、攻与耗之争。
        outcome: 石横以老兵之智定决战之策。
        arc_contribution: 决战战略定调。
        closing_pull: 军功派老将吐露朝中背景。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0077
        task: 士族空降兵临阵动摇，石横稳军心。
        preconditions:
          - 决战在即。
        conflict: 士族兵怯战欲逃。
        outcome: 石横以军规与气势压住，稳定阵脚。
        arc_contribution: 决战临门一稳。
        closing_pull: 妖潮大军压境。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0078
        task: 妖潮决战，石横血战妖王。
        preconditions:
          - 妖潮倾巢决战。
        conflict: 妖王凶悍、武夫力竭。
        outcome: 石横以命换妖王重创，首镇妖潮。
        arc_contribution: 卷目标条件二（首镇妖潮）达成。
        closing_pull: 妖王遁走，妖潮暂退。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0079
        task: 妖潮暂退，边关得喘息。
        preconditions:
          - 妖潮退去。
        conflict: 战后清算、伤亡抚恤。
        outcome: 石横镇后收拾残局，边关暂安。
        arc_contribution: 首镇妖潮战果落定。
        closing_pull: 妖潮退而不散，留有暗哨。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0080
        task: 论功清算，勘破"武夫为消耗品"真相一角。
        preconditions:
          - 妖潮暂定论功。
        conflict: 军功军饷被两层盘剥。
        outcome: 石横勘破消耗真相一角，完成 MS-ARC-002-03。
        arc_contribution: 卷目标条件二完成，真相主线立起。
        closing_pull: 朝中下发"妖患平，武夫减"文书。
        milestone: MS-ARC-002-03
        status: planned
      - id: CH-0081
        task: 妖潮暂定，边军整编，石横晋升。
        preconditions:
          - 妖患暂定。
        conflict: 整编中士族吞并军功派编制。
        outcome: 石横晋升什长，名望再涨。
        arc_contribution: 军中地位上升。
        closing_pull: 整编名单暗藏"削减武夫"条款。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0082
        task: 石横接触军需与粮政高层。
        preconditions:
          - 石横地位上升。
        conflict: 高层账目讳莫如深。
        outcome: 石横摸清军需粮政归口。
        arc_contribution: 消耗政策运作机制渐明。
        closing_pull: 军需官暗示"京里有人点头"。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0083
        task: 军中消耗政策全貌展开。
        preconditions:
          - 石横入军务核心。
        conflict: 武夫配额、伤亡补员、军功折算层层吃人。
        outcome: 石横看清武夫命价折算的全流程。
        arc_contribution: 卷目标条件三核心真相。
        closing_pull: 补员文书竟从血铺街式下线采买。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0084
        task: 掮客与京中世族粮道直接对接坐实。
        preconditions:
          - 石横握军需账。
        conflict: 军粮账与京中粮道印文吻合。
        outcome: 石横确认军中消耗政策即世族粮道一脉。
        arc_contribution: SEED-0001 卷二收官级推进。
        closing_pull: 掮客身份背后是世族管事。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0085
        task: 温白抽命线索与军中消耗政策同源坐实。
        preconditions:
          - 温白查血田。
        conflict: 血田与军饷同出京中世族。
        outcome: 石横温白合账，血田-粮道-消耗三线归一。
        arc_contribution: 全书同源吸血链成立。
        closing_pull: 血田名单出现军中伤兵名。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0086
        task: 军功派与士族制衡变化。
        preconditions:
          - 妖患暂定，朝局转。
        conflict: 士族乘势收编军功派。
        outcome: 石横居中周旋，保军功派元气。
        arc_contribution: 军中格局重构。
        closing_pull: 军功派老将被调离。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0087
        task: 北狄再集结，妖患余波。
        preconditions:
          - 边关喘息未定。
        conflict: 双压复起。
        outcome: 石横预判并加固防务。
        arc_contribution: 双压贯穿卷二。
        closing_pull: 北狄使者持朝中手令过境。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0088
        task: 石横暗中布局反制。
        preconditions:
          - 消耗真相集齐。
        conflict: 发作过早则人亡账空。
        outcome: 石横将账证分三处埋线。
        arc_contribution: 反制布局成型。
        closing_pull: 埋线被掮客耳目嗅到。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0089
        task: 妖患零星反扑，石横镇之。
        preconditions:
          - 妖潮余孽骚扰。
        conflict: 妖患不绝、人心思安。
        outcome: 石横清剿余孽，边关稍宁。
        arc_contribution: 妖线不灭，留待后卷。
        closing_pull: 余孽背后似有人为操纵。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0090
        task: 石禾病情反复，血田线索加深。
        preconditions:
          - 石禾长期用药。
        conflict: 药价飞涨、病根难除。
        outcome: 温白断言血田不除病难愈，石横入京之意更坚。
        arc_contribution: 石禾线保持张力，入京动机。
        closing_pull: 血田方位隐约指向京郊。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0091
        task: 军中妖丹军粮走私案发，牵出士族。
        preconditions:
          - 石横埋线取证。
        conflict: 案发牵连军功派。
        outcome: 石横以证据保住军功派，案指士族。
        arc_contribution: 反制初显成效。
        closing_pull: 士族反扑，欲调石横入死地。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0092
        task: 石横周旋保军功派，与士族正面结怨。
        preconditions:
          - 士族反扑。
        conflict: 军功派存亡一线。
        outcome: 石横借军规与舆论压回士族。
        arc_contribution: 军中派系博弈深化。
        closing_pull: 士族放出"京中贵人手令"。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0093
        task: 北狄大举试探，边关鏖战。
        preconditions:
          - 北狄增兵犯边。
        conflict: 妖患方息、北狄又至。
        outcome: 石横率军再战，稳住边关。
        arc_contribution: 北狄线再度加压。
        closing_pull: 北狄军中妖物重现。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0094
        task: 石横再立战功，勇卒之名传边关。
        preconditions:
          - 北狄战事。
        conflict: 以少敌众、险象环生。
        outcome: 石横阵斩敌将，名声传遍边关。
        arc_contribution: 军功与声望顶点。
        closing_pull: 京中军报点名石横。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0095
        task: 老卒遗愿落定，石横承诺查清旧账。
        preconditions:
          - 石横声望起。
        conflict: 旧账沉疴、遗愿未了。
        outcome: 石横以老卒遗愿为誓，账册再添一笔。
        arc_contribution: 袍泽旧账情感锚点。
        closing_pull: 旧账指向京中粮道。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0096
        task: 妖患余孽入村，石横护民。
        preconditions:
          - 妖患残害乡民。
        conflict: 妖孽披皮入村。
        outcome: 石横识破妖孽，护村灭妖。
        arc_contribution: 妖线不灭，护民延续。
        closing_pull: 妖孽身上带世族记号。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0097
        task: 猎妖行会深化合作，妖丹情报网成型。
        preconditions:
          - 石横与行会互信。
        conflict: 行会内部有世族眼线。
        outcome: 石横借行会织网，情报灵通。
        arc_contribution: 江湖线前置，卷三铺垫。
        closing_pull: 行会头目谈及京中妖丹行情。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0098
        task: 士族调令欲压石横。
        preconditions:
          - 石横声望碍眼。
        conflict: 明升暗降或遣死地。
        outcome: 石横识破调令，借军功拒之。
        arc_contribution: 反制士族压制。
        closing_pull: 朝中批复压至。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0099
        task: 石横反制调令，军中威望再高。
        preconditions:
          - 士族调令被拒。
        conflict: 朝令与军心相争。
        outcome: 石横以战功与军心为盾，稳住位置。
        arc_contribution: 军中话语权确立。
        closing_pull: 军功派老将密授入京引信。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0100
        task: 妖患彻底暂定，边关平稳。
        preconditions:
          - 妖患余波渐平。
        conflict: 太平表象下暗账汹涌。
        outcome: 石横借喘息整理账证，边关暂安。
        arc_contribution: 卷二中场收束。
        closing_pull: 京中粮价疯涨，边关粮荒将起。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0101
        task: 军中消耗政策证据集齐。
        preconditions:
          - 石横数年暗账。
        conflict: 账证人证俱全，发作时机未到。
        outcome: 石横完成消耗政策完整证据链。
        arc_contribution: 卷目标条件三证据面达成。
        closing_pull: 证据链指向粮道总账。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0102
        task: 石横埋线反制，证据分流。
        preconditions:
          - 证据集齐。
        conflict: 单线持证恐被毁。
        outcome: 石横将账证分交袍泽与江湖。
        arc_contribution: 反制布局完成。
        closing_pull: 掮客与世族闻风清查。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0103
        task: 温白随行查证，情愫正式确立。
        preconditions:
          - 石横温白生死与共。
        conflict: 入京之路凶险。
        outcome: 温白言明同行，女主线正式确立。
        arc_contribution: 卷目标条件二女主线达成。
        closing_pull: 石横望向京畿方向。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0104
        task: 北狄动静再起，边关军报入京。
        preconditions:
          - 北狄重整旗鼓。
        conflict: 军报需人呈送。
        outcome: 石横的妖患与北狄情报并入军报。
        arc_contribution: 入京引信升级。
        closing_pull: 京中传召军功将领。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0105
        task: 石横军功与妖患情报被京中注意。
        preconditions:
          - 军报入京。
        conflict: 各方争抢边功。
        outcome: 石横之名入京中权贵视野。
        arc_contribution: 入京动机与引子成型。
        closing_pull: 世族使节暗访武威营。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0106
        task: 世族招揽石横失败。
        preconditions:
          - 世族使节至。
        conflict: 高官厚禄诱石横站队。
        outcome: 石横不站队，拒招揽。
        arc_contribution: 立场确立，为卷三埋线。
        closing_pull: 世族放话"敬酒不吃"。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0107
        task: 军功派老将托付军功与情报。
        preconditions:
          - 老将知石横将行。
        conflict: 军中真相须人带出。
        outcome: 老将把军功名册与妖患情报托付石横。
        arc_contribution: 入京使命成型。
        closing_pull: 老将叮嘱"京里水深"。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0108
        task: 入京调令与邀功文书至。
        preconditions:
          - 军功与情报上达。
        conflict: 调令真假难辨。
        outcome: 石横识破半真半假的调令，决意顺水入京。
        arc_contribution: 入京契机制定。
        closing_pull: 调令上的官印与世族印文同源。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0109
        task: 石横权衡入京之局。
        preconditions:
          - 调令在手。
        conflict: 入京查账与赴死地并存。
        outcome: 石横定策：以军功为盾，入京查血田粮道。
        arc_contribution: 卷目标入京动机达成。
        closing_pull: 石禾病况成为入京最重砝码。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0110
        task: 安排石禾与温白随行。
        preconditions:
          - 石横定策入京。
        conflict: 军中旧账与家眷安置。
        outcome: 石横安排温白携石禾随行，袍泽留守。
        arc_contribution: 卷间角色布局。
        closing_pull: 离营之日将至。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0111
        task: 离营前交代袍泽，托付妖丹情报网。
        preconditions:
          - 石横将行。
        conflict: 情报网与反制线须留人。
        outcome: 石横将妖丹情报网与部分账证托付心腹。
        arc_contribution: 反制线留后手。
        closing_pull: 袍泽立誓守账。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0112
        task: 告别边关，携情报与军功北上。
        preconditions:
          - 石横离营。
        conflict: 送行与旧账难舍。
        outcome: 石横携妖患情报、军功名册北上入京。
        arc_contribution: 卷三入口开启。
        closing_pull: 官道尽头京畿方向。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0113
        task: 途中见世族渗透蔓延。
        preconditions:
          - 石横北行。
        conflict: 税令禁武悬赏粮价沿线更甚。
        outcome: 石横亲见世族渗透深广，SEED-0005 推进。
        arc_contribution: 卷三渗透铺垫落地。
        closing_pull: 沿路通缉画像似曾相识。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0114
        task: 押运妖丹遭劫。
        preconditions:
          - 石横受托押运妖丹。
        conflict: 劫匪有备而来。
        outcome: 石横识破劫局，护住妖丹。
        arc_contribution: 入京路风险展示。
        closing_pull: 劫匪背后的军需官印信。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0115
        task: 石横护妖丹，反查劫局。
        preconditions:
          - 妖丹安全。
        conflict: 反查牵出京中粮道。
        outcome: 石横顺藤摸瓜，再得一份证据。
        arc_contribution: 证据链加码。
        closing_pull: 劫局指使者浮出。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0116
        task: 近京畿，世族势力圈初见。
        preconditions:
          - 石横抵京郊。
        conflict: 官道驿站皆世族耳目。
        outcome: 石横初识京畿权力经纬。
        arc_contribution: 卷三地理舞台前置。
        closing_pull: 京郊庄园牌匾似曾相识。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0117
        task: 温白与石禾安置谋划。
        preconditions:
          - 石横入京在即。
        conflict: 京中无根基、药路未知。
        outcome: 石横谋定温白石禾落脚处。
        arc_contribution: 家眷线布局。
        closing_pull: 京中医馆有抽命病人。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0118
        task: 入京前夜合账，旧账全貌。
        preconditions:
          - 证据集齐。
        conflict: 账册残页医案军账合于一账。
        outcome: 石横合账，血田-粮道-消耗-军中全链清晰。
        arc_contribution: 卷一至卷二旧账总账成型。
        closing_pull: 总账缺环指向四大世族。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0119
        task: 京门在望，石横立卷末誓言。
        preconditions:
          - 石横抵京门。
        conflict: 明知京中吃人更深。
        outcome: 石横立誓查血田、清粮道、镇消耗。
        arc_contribution: 卷目标终态定调。
        closing_pull: 京门守卒查问军报。
        milestone: MS-ARC-002-04
        status: planned
      - id: CH-0120
        task: 入京，卷目标达成，铺设卷三。
        preconditions:
          - 石横入京。
        conflict: 京中粮道与血田暗流扑面。
        outcome: 石横携军功与妖患情报立足京城，完成 MS-ARC-002-04，卷目标达成。
        arc_contribution: 卷二收官：立身、首镇妖潮、勘破消耗真相，入京动机落定。
        closing_pull: 四大世族粮道博弈与血田阴影罩向石横。
        milestone: MS-ARC-002-04
        status: planned
  - id: ARC-003
    title: 京城世族·粮道风云
    start_chapter: 121
    end_chapter: 240
    planning_status: roadmap
    entry_cause: 石横因军功与妖患情报入京，卷入四大世族粮道之争，幼妹之病指向世族血田。
    goal:
      id: GOAL-ARC-003
      result: 石横查明世族血田如何"抽走凡人之命"，为幼妹找到续命路线，同时让世族粮道链条暴露一角。
      completion_conditions:
        - 四大世族粮道博弈中南侧链条被主角撕开。
        - 世族血田真相被确认并获得第一个直接证据。
        - 女主线正式确立，人际网由军转政。
      required_causality:
        - 世族血田与幼妹之病同源，与军中消耗政策同链。
        - 主角入京后仍保留乡邻与袍泽旧账。
      forbidden_outcomes:
        - 主角在京城直接灭掉四大世族。
        - 石禾之病被一次性治愈而失去跨卷张力。
      completion_evidence: 卷终正文、章节摘要及相关实体证据。
    milestones: []
    chapters: []
  - id: ARC-004
    title: 山外妖域·武圣遗体
    start_chapter: 241
    end_chapter: 360
    planning_status: roadmap
    entry_cause: 武圣遗体现世，各方争夺；主角为寻求救治幼妹与武夫命途的钥匙，率敢死队深入山外妖域。
    goal:
      id: GOAL-ARC-004
      result: 石横夺取薪火钥匙，拿到"人间焚武"第一层真相，确认武道盛世如何被上层联手抹掉。
      completion_conditions:
        - 妖域各族、驯妖/猎妖行会、武圣遗脉诸派与朝廷密使四方争夺中，主角夺钥。
        - 揭晓人间焚武历史真相的第一层。
        - 主角自武圣遗体处获得可传承的凡人武学薪火。
      required_causality:
        - 武圣遗体建设技术与世族血田、军中消耗政策具同源逻辑。
        - 薪火钥匙成为后续重建武藏的硬约束。
      forbidden_outcomes:
        - 妖域危机化解后妖线彻底消失。
        - 主角一次获得全部真相。
      completion_evidence: 卷终正文、章节摘要及相关实体证据。
    milestones: []
    chapters: []
  - id: ARC-005
    title: 京州烽火·诸郡逐鹿
    start_chapter: 361
    end_chapter: 480
    planning_status: roadmap
    entry_cause: 朝廷崩解、郡国并起，北狄铁骑南侵；主角携薪火与旧账归来，抢在群雄之前护武藏。
    goal:
      id: GOAL-ARC-005
      result: 主角在群雄逐鹿中确立护武藏主导权，联合义团教门与乡社，为最终重建武藏奠基。
      completion_conditions:
        - 主角在逐鹿中保住并扩大武藏火种。
        - 联军框架（江湖+乡社+义团）成型。
        - 暮年世族幕府与军阀矛盾充分暴露并被压制。
      required_causality:
        - 所有新结盟都以既有旧账为筹码，不做无根空降。
        - 北狄铁骑与妖患清剿两条外部压力贯穿全卷。
      forbidden_outcomes:
        - 主角在本卷即终结乱世。
        - 武藏火种被一次性清空。。
      completion_evidence: 卷终正文、章节摘要及相关实体证据。
    milestones: []
    chapters: []
  - id: ARC-006
    title: 武藏重立·凡武镇世
    start_chapter: 481
    end_chapter: 720
    planning_status: roadmap
    entry_cause: 乱世末程，主角以重建武藏为核心，联合江湖与乡社，对军阀世族残党与北狄妖患进行终局清算，确立人间凡武新秩序。
    goal:
      id: GOAL-ARC-006
      result: 重建人间武藏、终结乱世，确立"凡人皆可练武、不再卖血求生"的凡武正道。
      completion_conditions:
        - 武藏重新开放，普通凡人可习武。
        - 世族军阀残党、北狄、妖患被逐裁定镇。
        - 新朝重建起步，主角守护的新秩序得以确立。
      required_causality:
        - 终局建立在五卷累积的旧账、盟约与代价之上。
        - 每方旧敌的收束都由前期因果驱动，不做生硬清除。
      forbidden_outcomes:
        - 用神佛或"天道"这类非人间力量解决冲突。
        - 攻打世族与军阀、北狄、妖患时无成本推平。
      completion_evidence: 卷终正文、章节摘要及相关实体证据。
    milestones: []
    chapters: []
---

# 拳碎大魏 创作大纲

> YAML frontmatter 是卷路线图和章节执行契约的机器权威；下方内容是人类可读规划视图，与 frontmatter 同步。

## 1. 基本信息

| 字段 | 内容 |
| :--- | :--- |
| 书名 | 拳碎大魏 |
| 题材类型 | 古典乱世 · 武夫加点 · 极道流（玄幻/武侠融合） |
| 题材赛道 | 古典世界 + 极道流（肉身成圣、拳拳到肉、血气为薪） |
| 情绪闭环 | 生存恐惧 → 一拳破局 → 镇不平自己上 → 重建凡武正道 |
| 核心梗 | 以气血/寿元为薪的【破限加点】；杀人偿妙、身当武器 |
| 金手指/核心卖点 | 破限加点：消耗气血寿元换取肉身质变，胜利必有成本 |
| 平衡机制 | 寿元倒扣、妖患与北狄压力、世族垄断、乡邻伤亡 |
| 目标平台 | 番茄为主，全平台分发 |
| 预计总字数 | 约 200 万字（720 章节奏、单章 2300–2800 字） |
| 目标受众 | 番茄/起点古典武夫极道流读者；偏好拳拳到肉、凡人逆袭 |

## 2. 全书结构

| 阶段 | 章节范围 | 核心功能 | 必达结果 |
| :--- | :--- | :--- | :--- |
| 第一幕 | `CH-0001..0010` | 饥荒求生、金手指觉醒 | 卷目标达成，入伍离乡 |
| 第二幕 | `CH-0011..0240` | 边军与京城，消耗政策+粮道血田双线 | 幼妹续命线确立，世族链条露角 |
| 第三幕 | `CH-0241..0480` | 妖域真相与逐鹿烽火 | 薪火钥匙入手、武藏火种获保 |
| 第四幕 | `CH-0481..0720` | 重建武藏、凡武镇世 | 全书终局达成 |

## 3. 黄金三章与分卷循环

> **卷一（ARC-001）已归档**：黄金三章与卷内章节执行契约详情见 [archive/outline_history.md](archive/outline_history.md)。

## 4. 分卷路线图

| 卷 ID | 固定章节区间 | 卷目标 ID | 可验证终态 | 规划状态 |
| :--- | :--- | :--- | :--- | :--- |
| `ARC-001` | `CH-0001..0010` | `GOAL-ARC-001` | 击杀里正与豪强、名动乡里、武威营招揽 | frozen |
| `ARC-002` | `CH-0011..0120` | `GOAL-ARC-002` | 武威营立身、首镇妖潮、勘破消耗真相 | frozen |
| `ARC-003` | `CH-0121..0240` | `GOAL-ARC-003` | 查明血田、为幼妹找到续命路线 | roadmap |
| `ARC-004` | `CH-0241..0360` | `GOAL-ARC-004` | 夺薪火钥匙、拿到人间焚武第一层真相 | roadmap |
| `ARC-005` | `CH-0361..0480` | `GOAL-ARC-005` | 诸郡逐鹿中确立护武藏主导权、联军成型 | roadmap |
| `ARC-006` | `CH-0481..0720` | `GOAL-ARC-006` | 重建武藏、终结乱世、凡武正道确立 | roadmap |

## 5. 章节执行契约

> **卷一（ARC-001）已发布并归档**：`CH-0001..0010` 执行契约见 [archive/outline_history.md](archive/outline_history.md)。卷二（ARC-002）执行契约以 YAML frontmatter 为机器权威。

## 6. 情绪爆发点规划

> **卷一（ARC-001）已归档**：情绪爆发点 `HIT-ARC1-01..03` 见 [archive/outline_history.md](archive/outline_history.md)。

## 7. 核心设定摘要

| 维度 | 核心内容 | 关联文件 |
| :--- | :--- | :--- |
| 核心冲突 | 吃人的乱世秩序（世族/消耗政策/妖患）vs 凡人武夫的求生与守护 | |
| 主角初始处境 | 北方流民武夫，卖血被骗、濒死觉醒，护妹护乡 | `characters.md` |
| 力量体系摘要 | 皮肉力→筋骨阶→气血境→通脉→洗髓→腾龙→破限→神藏→镇世→武圣，共十阶 | `power.md` |
| 地理与势力格局 | 大魏末年：北疆流民地、边军武威营、京城世族、山外妖域、北狄草原、诸郡 | `geography.md` |
| 关键资源/道具 | 破限加点（机制）、妖丹、虎骨药、走私粮链账本、武圣遗体薪火钥匙 | `inventory.md` |
| 长线叙事线索 | 人间焚武真相、世族血田、军中被当消耗品、北狄妖患双压 | `hooks.md` |

## 8. 创作统计

| 字段 | 当前值 |
| :--- | :--- |
| 已完成章节数 | 10 |
| 累计字数 | 25672 |
| 当前完成进度 | 100% |
