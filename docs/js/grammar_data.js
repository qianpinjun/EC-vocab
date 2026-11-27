// Packet 4 (Unit 14: Adjective Clauses) Knowledge Points, Video Storyboards, Questions & Mind Maps

const GRAMMAR_TOPICS = [
    {
        id: 'kp1_placement',
        number: '01',
        title: '位置与基本结构 (Placement & Clauses)',
        subtitle: '独立分句 vs 从属分句；定语从句必须紧跟在所修饰的名词/代词后',
        badge: '基础架构',
        summary: 'Adjective clauses are dependent clauses placed directly after the noun or pronoun they modify (either after the object or inside the main clause right after the subject).',
        videoScenes: [
            {
                duration: 4500,
                badge: 'Scene 1 · 什么是定语从句',
                title: '把两个独立短句，合并成一个“主句 + 形容词性从句”',
                leftSentence: 'The professor emailed me.',
                rightSentence: 'He teaches Russian.',
                highlightTarget: 'The professor',
                highlightPronoun: 'He',
                resultSentence: 'The professor [who teaches Russian] emailed me.',
                cnTip: '从句就像一个超长形容词，必须紧贴在被修饰的名词（The professor）后面！',
                rulePill: '位置铁律：紧跟先行词 (Directly after noun/pronoun)'
            },
            {
                duration: 4500,
                badge: 'Scene 2 · 两种常见位置',
                title: '修饰宾语（句末） vs 修饰主语（句中插入）',
                leftSentence: '句末：They met a woman [who teaches psychology].',
                rightSentence: '句中：The woman [who teaches psychology] is also a writer.',
                highlightTarget: 'a woman / The woman',
                highlightPronoun: 'who',
                resultSentence: '注意：修饰主语时，从句夹在主语和主句谓语动词之间！',
                cnTip: '常见错误：把从句放到句尾 → ❌ The woman is a writer who teaches psychology.',
                rulePill: '修饰谁，就紧跟在谁的后面'
            },
            {
                duration: 4000,
                badge: 'Scene 3 · 独立 vs 依赖',
                title: 'Dependent Clause 不能单独成句',
                leftSentence: '✅ The house is in the suburbs. (Independent)',
                rightSentence: '❌ that we bought. (Dependent — 必须依附主句)',
                highlightTarget: 'The house',
                highlightPronoun: 'that',
                resultSentence: '✅ The house [that we bought] is in the suburbs.',
                cnTip: '看到 who / which / that 引导的片段，一定要检查主句是否还有完整的主谓！',
                rulePill: '主句完整 + 从句紧随其后'
            }
        ],
        questions: [
            {
                id: 'kp1_q1',
                type: 'combine',
                sourceTag: 'Packet 4 · B6 #2',
                prompt: '将下面两句话用定语从句合并为一句（注意从句紧跟所修饰的名词）：',
                sentences: ['The professor emailed me.', 'He teaches Russian.'],
                accepted: [
                    'The professor who teaches Russian emailed me.',
                    'The professor that teaches Russian emailed me.',
                    'The professor who emailed me teaches Russian.',
                    'The professor that emailed me teaches Russian.'
                ],
                sampleAnswer: 'The professor who teaches Russian emailed me.',
                hint: '“He” 指代 “The professor”，所以定语从句要紧跟在 “The professor” 后面。',
                mindMap: {
                    antecedent: 'The professor (主语 · 人)',
                    role: '在从句中作主语 (He → who / that)',
                    placement: '修饰主语，从句必须插在主语和 emailed me 之间',
                    trap: '切勿写成 "The professor emailed me who teaches Russian."（距离先行词太远）'
                }
            },
            {
                id: 'kp1_q2',
                type: 'combine',
                sourceTag: 'Packet 4 · B6 #5',
                prompt: '将下面两句话用定语从句合并为一句：',
                sentences: ['The little girl was crying.', 'She hurt her knee.'],
                accepted: [
                    'The little girl who hurt her knee was crying.',
                    'The little girl that hurt her knee was crying.',
                    'The little girl who was crying hurt her knee.',
                    'The little girl that was crying hurt her knee.'
                ],
                sampleAnswer: 'The little girl who hurt her knee was crying.',
                hint: '“She” 指代 “The little girl”，把第二句变成 who/that 从句紧跟在 girl 后面。',
                mindMap: {
                    antecedent: 'The little girl (人)',
                    role: '从句主语 (She → who / that)',
                    placement: '紧跟 The little girl 之后，主句谓语 was crying 在从句之后',
                    trap: '不要保留多余的 she（不可写 who she hurt）'
                }
            },
            {
                id: 'kp1_q3',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #1',
                prompt: '将下面两句话合并为一句（提示：把焦虑的特征放进定语从句修饰 Students）：',
                sentences: ['Students do well on tests if they are prepared beforehand.', 'Some students are anxious.'],
                accepted: [
                    'Students who are anxious do well on tests if they are prepared beforehand.',
                    'Students that are anxious do well on tests if they are prepared beforehand.',
                    'Some students who are anxious do well on tests if they are prepared beforehand.',
                    'Some students that are anxious do well on tests if they are prepared beforehand.'
                ],
                sampleAnswer: 'Students who are anxious do well on tests if they are prepared beforehand.',
                hint: '先找主句骨架 "Students do well on tests..."，把 "are anxious" 变成 "who/that are anxious" 紧贴 Students。',
                mindMap: {
                    antecedent: 'Students (复数 · 人)',
                    role: '从句主语 (who / that + are)',
                    placement: '主句主语后直接插入 who are anxious',
                    trap: '主句已经有 do well，不能把 Students 放到最后；复数配 are'
                }
            },
            {
                id: 'kp1_q4',
                type: 'combine',
                sourceTag: 'Packet 4 · B6 #8',
                prompt: '将下面两句话用定语从句合并为一句：',
                sentences: ['The child went home.', 'He was sick.'],
                accepted: [
                    'The child who was sick went home.',
                    'The child that was sick went home.',
                    'The child who went home was sick.',
                    'The child that went home was sick.'
                ],
                sampleAnswer: 'The child who was sick went home.',
                hint: '“He” 指代 “The child”，从句紧跟 The child。',
                mindMap: {
                    antecedent: 'The child (人)',
                    role: '从句主语 (He → who / that)',
                    placement: 'The child [who was sick] went home.',
                    trap: '不能把 who was sick 放在 went home 后面（否则变成修饰 home）'
                }
            },
            {
                id: 'kp1_q5',
                type: 'multi',
                sourceTag: 'Packet 4 · Grammar Note 1',
                prompt: '选出所有语法与语序完全正确的合并句子（可多选）：',
                sentence: '判断以下哪句正确合并了 “The car is outside.” + “It belongs to my uncle.”：',
                options: [
                    'The car that belongs to my uncle is outside.',
                    'The car which belongs to my uncle is outside.',
                    'The car is outside that belongs to my uncle.',
                    'The car which it belongs to my uncle is outside.'
                ],
                correctAnswers: [
                    'The car that belongs to my uncle is outside.',
                    'The car which belongs to my uncle is outside.'
                ],
                hint: '修饰物可用 which/that；从句必须紧跟 The car，且不能多出 it。',
                mindMap: {
                    antecedent: 'The car (物)',
                    role: '从句主语 (which / that)',
                    placement: '必须紧跟 The car，不可拆开到 is outside 后面',
                    trap: '错误选项 3 位置错位；错误选项 4 犯了双主语 (which it) 错误'
                }
            },
            {
                id: 'kp1_q6',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 1',
                prompt: '选出所有语序正确且无多余代词的句子（可多选）：',
                sentence: '判断以下哪句正确合并了 “The student won the debate.” + “She wrote the opening essay.”：',
                options: [
                    'The student who wrote the opening essay won the debate.',
                    'The student that wrote the opening essay won the debate.',
                    'The student won the debate who wrote the opening essay.',
                    'The student who she wrote the opening essay won the debate.'
                ],
                correctAnswers: [
                    'The student who wrote the opening essay won the debate.',
                    'The student that wrote the opening essay won the debate.'
                ],
                hint: '定语从句必须紧插在主语 The student 后面，且删除重复主语 she。',
                mindMap: {
                    antecedent: 'The student (主语 · 人)',
                    role: '从句主语 (She → who / that)',
                    placement: '紧贴 The student，放在 won the debate 之前',
                    trap: '选项 3 把从句误放到了 debate 后面；选项 4 多余保留了 she'
                }
            },
            {
                id: 'kp1_q7',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 2',
                prompt: '识别完整句 vs 残缺从句：选出所有【语法完整、可独立成句】的选项：',
                sentence: '判断下面哪些句子是完整的独立句（Independent + Dependent 正确结合）：',
                options: [
                    'The library that opened last autumn has quiet study rooms.',
                    'Which opened last autumn near the main campus gate.',
                    'We visited a museum that displayed ancient maps.',
                    'The laptop that I ordered online yesterday afternoon.'
                ],
                correctAnswers: [
                    'The library that opened last autumn has quiet study rooms.',
                    'We visited a museum that displayed ancient maps.'
                ],
                hint: '检查主句是否有完整的谓语动词！选项 2 只有从句，选项 4 主语 The laptop 后面缺少主句谓语动词。',
                mindMap: {
                    antecedent: 'The library / a museum',
                    role: '辨析完整主句 vs 残缺片段 (Fragment)',
                    placement: '从句只能修饰名词，不能替代主句谓语',
                    trap: '选项 4 看似很长，但主句缺少谓语动词，属于典型残缺句！'
                }
            },
            {
                id: 'kp1_q8',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 3',
                prompt: '选出所有将定语从句放在【正确先行词后】的句子：',
                sentence: '想表达“那位站在讲台旁的老师表扬了我们”，哪些写法位置正确？',
                options: [
                    'The teacher who stood beside the podium praised us.',
                    'The teacher that stood beside the podium praised us.',
                    'The teacher praised us who stood beside the podium.',
                    'Who stood beside the podium the teacher praised us.'
                ],
                correctAnswers: [
                    'The teacher who stood beside the podium praised us.',
                    'The teacher that stood beside the podium praised us.'
                ],
                hint: 'who stood beside the podium 修饰的是 The teacher，必须紧贴 The teacher。',
                mindMap: {
                    antecedent: 'The teacher (人)',
                    role: '从句主语 (who / that)',
                    placement: '修饰主语时插在主语和主句动词 praised 之间',
                    trap: '不能把定语从句放到 us 后面，也不能放到主语前面'
                }
            },
            {
                id: 'kp1_q9',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 4',
                prompt: '选出所有语法正确的句子（修饰宾语位置）：',
                sentence: '合并 “Maya read an article.” + “It explained coastal erosion.”：',
                options: [
                    'Maya read an article that explained coastal erosion.',
                    'Maya read an article which explained coastal erosion.',
                    'Maya who read an article explained coastal erosion.',
                    'Maya read an article that it explained coastal erosion.'
                ],
                correctAnswers: [
                    'Maya read an article that explained coastal erosion.',
                    'Maya read an article which explained coastal erosion.'
                ],
                hint: 'It 指代宾语 an article，所以从句紧跟在 an article 后面，用 that 或 which。',
                mindMap: {
                    antecedent: 'an article (宾语 · 物)',
                    role: '从句主语 (It → that / which)',
                    placement: '直接紧跟宾语 an article 之后',
                    trap: '选项 3 改错了修饰对象；选项 4 犯了双主语 (that it) 错误'
                }
            },
            {
                id: 'kp1_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 1',
                prompt: '将下面两句话用定语从句合并为一句（注意从句紧跟所修饰的主语）：',
                sentences: ['The scientist won a national prize.', 'She discovered the new vaccine.'],
                accepted: [
                    'The scientist who discovered the new vaccine won a national prize.',
                    'The scientist that discovered the new vaccine won a national prize.',
                    'The scientist who won a national prize discovered the new vaccine.',
                    'The scientist that won a national prize discovered the new vaccine.'
                ],
                sampleAnswer: 'The scientist who discovered the new vaccine won a national prize.',
                hint: 'She 指代 The scientist，将 who/that discovered the new vaccine 紧插在 The scientist 后面。',
                mindMap: {
                    antecedent: 'The scientist (主语 · 人)',
                    role: '从句主语 (She → who / that)',
                    placement: 'The scientist [who discovered the new vaccine] won...',
                    trap: '不能把从句放到 prize 后面，也不要保留 she'
                }
            }
        ]
    },
    {
        id: 'kp2_subjects',
        number: '02',
        title: '作主语的关系代词 (who / which / that)',
        subtitle: '指人用 who/that，指物用 which/that；注意主谓一致与禁止双主语',
        badge: '高频考点',
        summary: 'Use who/that for people and which/that for things as subjects. The verb inside the clause agrees with the antecedent, and never repeat the subject (NO "who he" or "which it").',
        videoScenes: [
            {
                duration: 4500,
                badge: 'Scene 1 · 指人 vs 指物',
                title: '作主语时：谁对应谁？',
                leftSentence: '人 (People)：who / that（that 更口语）',
                rightSentence: '物 (Things)：which / that',
                highlightTarget: 'people / book',
                highlightPronoun: 'who / which / that',
                resultSentence: '⚠️ 作主语时，关系代词绝对【不能省略 (Ø)】！',
                cnTip: '记住：Ann is a person which... ❌ 绝对不能用 which 指代人！',
                rulePill: '人: who/that | 物: which/that | 主语不可省'
            },
            {
                duration: 4500,
                badge: 'Scene 2 · 两大必避雷区',
                title: '雷区① 双主语 (Double Subject) & 雷区② 主谓一致',
                leftSentence: '❌ Type C individuals are people who THEY love data.',
                rightSentence: '❌ There are many people who HAS taken this test.',
                highlightTarget: 'many people (复数)',
                highlightPronoun: 'who',
                resultSentence: '✅ ...people who love data. / ✅ ...many people who HAVE taken...',
                cnTip: 'who 已经顶替了主语位置，后面绝不能再留 he / she / it / they！动词单复数看前面的先行词！',
                rulePill: '删掉原主语代词 + 动词随先行词变单复数'
            }
        ],
        questions: [
            {
                id: 'kp2_q1',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #10',
                prompt: '选出所有可以填入括号的正确选项（可能不止一个）：',
                sentence: 'Anyone ( ______ ) enjoyed Pirates of the Caribbean will love this movie.',
                options: ['who', 'whom', 'that', 'Ø'],
                correctAnswers: ['who', 'that'],
                hint: 'Anyone 指人，且空格后面直接跟动词 enjoyed，说明关系词在从句中作【主语】。',
                mindMap: {
                    antecedent: 'Anyone (人)',
                    role: '作从句主语 (后接动词 enjoyed)',
                    placement: '限定性定语从句（无逗号）',
                    trap: 'whom 只能作宾语；主语位置绝对不能省略 (Ø)！'
                }
            },
            {
                id: 'kp2_q2',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #1',
                prompt: '选出所有可以填入括号的正确选项：',
                sentence: 'The lady ( ______ ) is my teacher is the third from the right.',
                options: ['who', 'which', 'that', 'whom'],
                correctAnswers: ['who', 'that'],
                hint: 'The lady 指人，空格后是系动词 is（作主语）。',
                mindMap: {
                    antecedent: 'The lady (人)',
                    role: '作从句主语 (后接 is)',
                    placement: '无逗号限定性从句',
                    trap: 'which 不能指人；whom 不能作主语'
                }
            },
            {
                id: 'kp2_q3',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #8',
                prompt: '选出唯一正确的选项：',
                sentence: 'Chuy is a person ( ______ ) prefers to be alone.',
                options: ['who', 'who he', 'which', 'Ø'],
                correctAnswers: ['who'],
                hint: '小心双主语陷阱！who 本身就是主语。',
                mindMap: {
                    antecedent: 'a person (人)',
                    role: '作从句主语 (prefers)',
                    placement: '限定性从句',
                    trap: 'who he 属于“双主语”致命错误；which 不能指人；作主语不能省略'
                }
            },
            {
                id: 'kp2_q4',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #7 & Note 2',
                prompt: '选出正确的动词形式（注意主谓一致）：',
                sentence: 'Lions are the animals that Lea ( ______ ) the best.',
                options: ['like', 'likes'],
                correctAnswers: ['likes'],
                hint: '看清楚从句里的主语是谁！不是 Lions，也不是 animals，而是 Lea！',
                mindMap: {
                    antecedent: 'the animals (作 likes 的宾语)',
                    role: 'that 作从句宾语，从句真正的主语是 Lea (第三人称单数)',
                    placement: '主谓一致看从句主语 Lea（而非前面的复数 animals）',
                    trap: '不要被前面的复数 Lions / animals 迷惑而误选 like'
                }
            },
            {
                id: 'kp2_q5',
                type: 'combine',
                sourceTag: 'Packet 4 · B6 #1',
                prompt: '用 who / that / which 将两句合并为一句：',
                sentences: ['I picked up the package.', 'It was lying on the front step.'],
                accepted: [
                    'I picked up the package that was lying on the front step.',
                    'I picked up the package which was lying on the front step.',
                    'The package that I picked up was lying on the front step.',
                    'The package which I picked up was lying on the front step.'
                ],
                sampleAnswer: 'I picked up the package that was lying on the front step.',
                hint: 'package 是物，用 that 或 which 替换 It。',
                mindMap: {
                    antecedent: 'the package (物)',
                    role: '从句主语 (It → that / which)',
                    placement: '直接接在 the package 后',
                    trap: '不能保留 it（❌ that it was lying），且不能省略 that/which'
                }
            },
            {
                id: 'kp2_q6',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #5',
                prompt: '用定语从句合并下面两句话：',
                sentences: ['Recently, a large airplane had a serious accident.', 'It was carrying too many passengers.'],
                accepted: [
                    'Recently, a large airplane that was carrying too many passengers had a serious accident.',
                    'Recently, a large airplane which was carrying too many passengers had a serious accident.'
                ],
                sampleAnswer: 'Recently, a large airplane that was carrying too many passengers had a serious accident.',
                hint: 'It 指代 a large airplane，把第二句变成定语从句紧跟在 airplane 后面。',
                mindMap: {
                    antecedent: 'a large airplane (物)',
                    role: '从句主语 (It → that / which)',
                    placement: '插在 airplane 与 had 之间',
                    trap: '记得删掉 It，且不要把从句放到 accident 后面'
                }
            },
            {
                id: 'kp2_q7',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 5',
                prompt: '选出所有可以填入括号的正确选项（注意主谓一致与指物规则）：',
                sentence: 'The bridge ( ______ ) connects the two islands was built in 1962.',
                options: ['which', 'that', 'who', 'Ø'],
                correctAnswers: ['which', 'that'],
                hint: 'The bridge 是物，且空格后紧跟动词 connects（作主语），所以只能选 which 或 that，不能省略 Ø！',
                mindMap: {
                    antecedent: 'The bridge (单数 · 物)',
                    role: '作从句主语 (connects)',
                    placement: '限定性定语从句',
                    trap: 'who 只能指人；关系代词作主语时绝不可省略 Ø'
                }
            },
            {
                id: 'kp2_q8',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 2',
                prompt: '用 who 或 that 将下面两句话合并为一句：',
                sentences: ['The volunteer spoke three languages.', 'He guided the visitors through the hall.'],
                accepted: [
                    'The volunteer who guided the visitors through the hall spoke three languages.',
                    'The volunteer that guided the visitors through the hall spoke three languages.',
                    'The volunteer who spoke three languages guided the visitors through the hall.',
                    'The volunteer that spoke three languages guided the visitors through the hall.'
                ],
                sampleAnswer: 'The volunteer who guided the visitors through the hall spoke three languages.',
                hint: 'He 指代 The volunteer（人），用 who / that 替换 He 并紧跟在 The volunteer 后面。',
                mindMap: {
                    antecedent: 'The volunteer (人)',
                    role: '从句主语 (He → who / that)',
                    placement: '插在 The volunteer 与主句谓语之间',
                    trap: '删除多余主语 He，不可写成 who he guided'
                }
            },
            {
                id: 'kp2_q9',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 3',
                prompt: '用 which 或 that 将下面两句话合并为一句：',
                sentences: ['We bought a dictionary.', 'It includes clear grammar examples.'],
                accepted: [
                    'We bought a dictionary that includes clear grammar examples.',
                    'We bought a dictionary which includes clear grammar examples.'
                ],
                sampleAnswer: 'We bought a dictionary that includes clear grammar examples.',
                hint: 'It 指代 a dictionary（物），删掉 It 换成 that 或 which。',
                mindMap: {
                    antecedent: 'a dictionary (单数 · 物)',
                    role: '从句主语 (It → that / which)',
                    placement: '直接接在 a dictionary 后面',
                    trap: '作主语不可省略，且动词 includes 保持单数'
                }
            },
            {
                id: 'kp2_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 4',
                prompt: '用定语从句合并下面两句话（注意复数先行词与谓语动词一致）：',
                sentences: ['The engineers designed a safer bridge.', 'They worked on the river project.'],
                accepted: [
                    'The engineers who worked on the river project designed a safer bridge.',
                    'The engineers that worked on the river project designed a safer bridge.',
                    'The engineers who designed a safer bridge worked on the river project.',
                    'The engineers that designed a safer bridge worked on the river project.'
                ],
                sampleAnswer: 'The engineers who worked on the river project designed a safer bridge.',
                hint: 'They 指代 The engineers（人），用 who / that 替换 They 紧跟在 The engineers 后面。',
                mindMap: {
                    antecedent: 'The engineers (复数 · 人)',
                    role: '从句主语 (They → who / that)',
                    placement: 'The engineers [who worked on the river project] designed...',
                    trap: '不能保留 they（❌ who they worked）'
                }
            }
        ]
    },
    {
        id: 'kp3_objects',
        number: '03',
        title: '作宾语与省略 (who(m) / which / that / Ø)',
        subtitle: '作动词或介词宾语时可省略关系代词 (Ø)；注意“介词+whom/which”的特殊限制',
        badge: '易错难点',
        summary: 'When the relative pronoun is an object in an identifying clause, you can omit it (Ø). If a preposition comes right before the pronoun, you MUST use whom (people) or which (things) — never that or Ø.',
        videoScenes: [
            {
                duration: 4500,
                badge: 'Scene 1 · 作宾语可以省略 (Ø)',
                title: '当从句里已经有“主语 + 动词”时，关系词就是宾语！',
                leftSentence: 'The test [which / that / Ø] I took was difficult.',
                rightSentence: 'The politician [who / whom / that / Ø] I respect...',
                highlightTarget: 'I took / I respect',
                highlightPronoun: 'Ø (可省略)',
                resultSentence: '判断口诀：空格后紧跟【另一个主语(I/Mary/we)】，即可用 Ø！',
                cnTip: '注意：人作宾语时，正式用 whom，口语常用 who / that / Ø。',
                rulePill: '限定性作宾语 → 可省略 (Ø)'
            },
            {
                duration: 5000,
                badge: 'Scene 2 · 介词前置陷阱 (Preposition Trap)',
                title: '介词在从句末尾 vs 介词提前到关系词前！',
                leftSentence: '介词在句末：The man (who/whom/that/Ø) I gave the money TO.',
                rightSentence: '句末没有介词：The man (TO WHOM) I gave the money.',
                highlightTarget: 'gave the money (缺少 to)',
                highlightPronoun: 'to whom / to which',
                resultSentence: '⚠️ 介词后面只能用 whom / which，绝不能用 that 或 Ø！',
                cnTip: '例：think ABOUT it → It’s a situation (that/which/Ø) I’d rather not think ABOUT（句末已有 about，不能再选 to which！）。',
                rulePill: '介词在后随便选；介词在前只用 whom / which'
            }
        ],
        questions: [
            {
                id: 'kp3_q1',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #1',
                prompt: '选出所有可以填入括号的正确选项（注意句中已有 next to）：',
                sentence: 'The girl ( ______ ) I sat next to in math class always knew the answers.',
                options: ['that', 'who', 'which', 'Ø'],
                correctAnswers: ['that', 'who', 'Ø'],
                hint: 'The girl 指人；I sat next to 缺宾语（介词 to 在后面）。',
                mindMap: {
                    antecedent: 'The girl (人)',
                    role: '作介词 next to 的宾语 (I sat next to her)',
                    placement: '限定性从句，介词在后',
                    trap: 'which 不能指代人！人作宾语时 that / who / Ø 都可以'
                }
            },
            {
                id: 'kp3_q2',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #4',
                prompt: '选出所有可以填入括号的正确选项（注意句末已有 about）：',
                sentence: "It's a situation ( ______ ) I'd rather not think about.",
                options: ['that', 'which', 'to which'],
                correctAnswers: ['that', 'which'],
                hint: '动词搭配是 think about，句子末尾已经有 about，而且不能用 to！',
                mindMap: {
                    antecedent: 'a situation (物)',
                    role: '作 think about 的宾语',
                    placement: 'about 留在句末',
                    trap: '选 to which 会变成 "to which ... think about"，不仅介词多余而且搭配错误'
                }
            },
            {
                id: 'kp3_q3',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #7',
                prompt: '选出所有可以填入括号的正确选项：',
                sentence: 'Nelson Mandela is a politician ( ______ ) I respect a lot.',
                options: ['who', 'whom', 'Ø'],
                correctAnswers: ['who', 'whom', 'Ø'],
                hint: 'politician 指人；I respect 缺宾语（无逗号）。',
                mindMap: {
                    antecedent: 'a politician (人)',
                    role: '作动词 respect 的宾语',
                    placement: '限定性从句（无逗号）',
                    trap: '作宾语时 who / whom / Ø 全对（whom 较正式，Ø 最口语）'
                }
            },
            {
                id: 'kp3_q4',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #11',
                prompt: '选出唯一正确的选项（仔细看 money 后面有没有介词 to！）：',
                sentence: "I didn't see the face of the man ( ______ ) I gave the money.",
                options: ['who', 'whom', 'to whom'],
                correctAnswers: ['to whom'],
                hint: '原句是 I gave the money TO the man！这里 money 后面没有 to，所以必须把 to 带在关系词前面！',
                mindMap: {
                    antecedent: 'the man (人)',
                    role: 'give sth. TO sb.（需要介词 to）',
                    placement: '句末缺少 to，必须用介词前置 to whom',
                    trap: '如果直接填 who/whom，意思就缺少了“给（某人）”所需的介词 to'
                }
            },
            {
                id: 'kp3_q5',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #7',
                prompt: '将下面两句话合并为一句（可使用 that / which 或省略关系词）：',
                sentences: ['The dress was long, black, and beautiful.', 'Mary wore it.'],
                accepted: [
                    'The dress that Mary wore was long, black, and beautiful.',
                    'The dress which Mary wore was long, black, and beautiful.',
                    'The dress Mary wore was long, black, and beautiful.',
                    'Mary wore the dress that was long, black, and beautiful.',
                    'Mary wore the dress which was long, black, and beautiful.'
                ],
                sampleAnswer: 'The dress that Mary wore was long, black, and beautiful.',
                hint: 'it 指代 The dress，在 Mary wore it 中作宾语。记住删掉 it！',
                mindMap: {
                    antecedent: 'The dress (物)',
                    role: '作 wore 的宾语 (it → that / which / Ø)',
                    placement: '紧跟 The dress 后：The dress [that Mary wore] was...',
                    trap: '千万别保留 it（❌ that Mary wore it）'
                }
            },
            {
                id: 'kp3_q6',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #8',
                prompt: '将下面两句话合并为一句：',
                sentences: ['On my vacation, I met a boy.', 'My father disliked him.'],
                accepted: [
                    'On my vacation, I met a boy who my father disliked.',
                    'On my vacation, I met a boy whom my father disliked.',
                    'On my vacation, I met a boy that my father disliked.',
                    'On my vacation, I met a boy my father disliked.'
                ],
                sampleAnswer: 'On my vacation, I met a boy whom my father disliked.',
                hint: 'him 指代 a boy，在从句中作 disliked 的宾语，必须删掉 him。',
                mindMap: {
                    antecedent: 'a boy (人)',
                    role: '作 disliked 的宾语 (him → who / whom / that / Ø)',
                    placement: '紧跟 a boy 之后',
                    trap: '不要在句末保留 him（❌ whom my father disliked him）'
                }
            },
            {
                id: 'kp3_q7',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 6',
                prompt: '选出所有可以填入括号的正确选项（注意介词 for 已经在句末）：',
                sentence: 'The scholarship ( ______ ) she applied for covers full tuition.',
                options: ['that', 'which', 'Ø', 'for which'],
                correctAnswers: ['that', 'which', 'Ø'],
                hint: '句末已经有 for 了！不能再选 for which（否则重复两个 for）；物作限定性宾语时 that / which / Ø 全对！',
                mindMap: {
                    antecedent: 'The scholarship (物)',
                    role: '作 applied for 的宾语',
                    placement: '介词 for 留在句末',
                    trap: '若选 for which 会造成 “for which ... applied for” 介词重复错误！'
                }
            },
            {
                id: 'kp3_q8',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 5',
                prompt: '将下面两句话合并为一句（可使用 that / which 或省略关系词）：',
                sentences: ['The novel was inspiring.', 'Our English teacher recommended it.'],
                accepted: [
                    'The novel that our English teacher recommended was inspiring.',
                    'The novel which our English teacher recommended was inspiring.',
                    'The novel our English teacher recommended was inspiring.'
                ],
                sampleAnswer: 'The novel that our English teacher recommended was inspiring.',
                hint: 'it 指代 The novel 作 recommended 的宾语，必须删掉 it，紧跟在 The novel 后面。',
                mindMap: {
                    antecedent: 'The novel (物)',
                    role: '作 recommended 的宾语 (it → that / which / Ø)',
                    placement: 'The novel [that our English teacher recommended] was inspiring.',
                    trap: '千万不能在 recommended 后保留 it！'
                }
            },
            {
                id: 'kp3_q9',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 6',
                prompt: '将下面两句话合并为一句（注意删掉多余的宾语 her）：',
                sentences: ['The architect moved to Seattle.', 'We interviewed her last Friday.'],
                accepted: [
                    'The architect who we interviewed last Friday moved to Seattle.',
                    'The architect whom we interviewed last Friday moved to Seattle.',
                    'The architect that we interviewed last Friday moved to Seattle.',
                    'The architect we interviewed last Friday moved to Seattle.'
                ],
                sampleAnswer: 'The architect whom we interviewed last Friday moved to Seattle.',
                hint: 'her 指代 The architect 作 interviewed 的宾语，删掉 her，用 who / whom / that 或省略连接。',
                mindMap: {
                    antecedent: 'The architect (人)',
                    role: '作 interviewed 的宾语 (her → who / whom / that / Ø)',
                    placement: 'The architect [whom we interviewed last Friday] moved...',
                    trap: '切勿保留 her（❌ whom we interviewed her last Friday）'
                }
            },
            {
                id: 'kp3_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 7',
                prompt: '将下面两句话合并为一句（介词 to 可保留在句末，或提前写成 to whom）：',
                sentences: ['The advisor was very patient.', 'I spoke to him after class.'],
                accepted: [
                    'The advisor who I spoke to after class was very patient.',
                    'The advisor whom I spoke to after class was very patient.',
                    'The advisor that I spoke to after class was very patient.',
                    'The advisor I spoke to after class was very patient.',
                    'The advisor to whom I spoke after class was very patient.'
                ],
                sampleAnswer: 'The advisor whom I spoke to after class was very patient.',
                hint: 'him 指代 The advisor，删掉 him；介词 to 留在 spoke 后可用 who/whom/that/Ø，提前则用 to whom。',
                mindMap: {
                    antecedent: 'The advisor (人)',
                    role: '作介词 to 的宾语',
                    placement: '紧跟 The advisor 之后',
                    trap: '若把 to 提前，只能写 to whom（绝不能写 to who 或 to that）'
                }
            }
        ]
    },
    {
        id: 'kp4_whose',
        number: '04',
        title: '所有格关系词 (whose + Noun)',
        subtitle: '替代 his / her / its / their + 名词；指人指物都可以，且绝不能省略',
        badge: '必考结构',
        summary: 'Use whose + noun to replace his/her/its/their + noun (for both people and things). Whose can NEVER be omitted.',
        videoScenes: [
            {
                duration: 4500,
                badge: 'Scene 1 · whose = 某人/某物的',
                title: '如何识别什么时候该用 whose？',
                leftSentence: 'Ken is the man. + We met HIS wife.',
                rightSentence: "It's a theory. + ITS origins go back many years.",
                highlightTarget: 'HIS wife / ITS origins',
                highlightPronoun: 'whose',
                resultSentence: 'Ken is the man [whose wife] we met. / ...[whose origins] go back...',
                cnTip: '秘诀：看到空格后面紧跟一个【光杆名词】（无 a/the/my），如 whose name / whose dog / whose car，就选 whose！',
                rulePill: 'whose + 名词（人/物通用，绝不可省略）'
            }
        ],
        questions: [
            {
                id: 'kp4_q1',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #3',
                prompt: '选出唯一正确的选项：',
                sentence: 'My grandmother, ( ______ ) maiden name was Faust, grew up in Germany.',
                options: ['who', 'which', 'whose'],
                correctAnswers: ['whose'],
                hint: 'maiden name（婚前姓氏）是属于 grandmother 的（her maiden name）。',
                mindMap: {
                    antecedent: 'My grandmother (人)',
                    role: '作定语修饰 maiden name (her maiden name → whose maiden name)',
                    placement: '非限定性从句（有逗号）',
                    trap: 'who 不能直接修饰名词 maiden name'
                }
            },
            {
                id: 'kp4_q2',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #5',
                prompt: '选出唯一正确的选项：',
                sentence: 'I saw a former professor of mine ( ______ ) name I can never remember.',
                options: ['that', 'whose', 'whom'],
                correctAnswers: ['whose'],
                hint: '“whose name” = his/her name（他的名字我老记不住）。',
                mindMap: {
                    antecedent: 'a former professor of mine (人)',
                    role: '所属关系：professor’s name → whose name',
                    placement: '限定性从句',
                    trap: 'that / whom 后面不能直接加名词 name'
                }
            },
            {
                id: 'kp4_q3',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #4',
                prompt: '选出唯一正确的选项：',
                sentence: "The man ( ______ ) car we borrowed is my father's boss.",
                options: ['whose', 'which', 'who', 'Ø'],
                correctAnswers: ['whose'],
                hint: 'we borrowed HIS car → whose car we borrowed。',
                mindMap: {
                    antecedent: 'The man (人)',
                    role: 'his car → whose car（在从句中作 borrowed 的宾语）',
                    placement: '修饰主语 The man',
                    trap: 'whose 永远不能省略 (Ø)，也不能换成 which'
                }
            },
            {
                id: 'kp4_q4',
                type: 'multi',
                sourceTag: 'Packet 4 · Grammar Note 4',
                prompt: '判断：whose 能否修饰“事物”（例如 book, theory）？选出所有正确句子：',
                sentence: '选出以下所有语法正确的句子：',
                options: [
                    "It's a theory whose origins go back many years.",
                    "It's the book whose reviews were so good.",
                    'Harvey, house we are renting, is a lawyer.',
                    "It's a theory which origins go back many years."
                ],
                correctAnswers: [
                    "It's a theory whose origins go back many years.",
                    "It's the book whose reviews were so good."
                ],
                hint: 'whose 既可用于人，也可用于物（替代 its）；并且 whose 永远不能省略！',
                mindMap: {
                    antecedent: 'a theory / the book (物)',
                    role: 'its origins / its reviews → whose origins / whose reviews',
                    placement: 'whose + 名词',
                    trap: '第3句省略了 whose (❌)；第4句误用了 which 代替所有格 (❌)'
                }
            },
            {
                id: 'kp4_q5',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #9',
                prompt: '把下面三句话合成为一句话（同时练习 whose 与非限定性 which）：',
                sentences: [
                    'Jacob is a student in my biology class.',
                    'His father is the ambassador from Kenya.',
                    'The class meets twice a week.'
                ],
                accepted: [
                    'Jacob, whose father is the ambassador from Kenya, is a student in my biology class, which meets twice a week.'
                ],
                sampleAnswer: 'Jacob, whose father is the ambassador from Kenya, is a student in my biology class, which meets twice a week.',
                hint: 'His father → whose father（修饰专有名词 Jacob，前后需加逗号）；The class → , which meets twice a week（非限定性从句需加逗号并用 which）。',
                mindMap: {
                    antecedent: 'Jacob (专有名词) + my biology class (特指)',
                    role: 'His father → whose father；The class → , which',
                    placement: '两个非限定性从句分别用逗号紧跟 Jacob 和 my biology class',
                    trap: 'Jacob 是专有名词且 my biology class 为特定课程，两处从句均需逗号，逗号后禁用 that'
                }
            },
            {
                id: 'kp4_q6',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 7',
                prompt: '选出唯一正确的选项（空格后紧跟光杆名词 roof）：',
                sentence: 'They repaired the old barn ( ______ ) roof had leaked during the storm.',
                options: ['which', 'whose', 'that', 'Ø'],
                correctAnswers: ['whose'],
                hint: 'roof 属于 the old barn（its roof → whose roof），whose 可以修饰物且绝不可省略！',
                mindMap: {
                    antecedent: 'the old barn (物)',
                    role: 'its roof → whose roof',
                    placement: 'whose + 名词 roof',
                    trap: '不能用 which / that 直接加名词，也不能省略 whose'
                }
            },
            {
                id: 'kp4_q7',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 8',
                prompt: '用 whose 将下面两句话合并为一句：',
                sentences: ['I thanked the neighbor.', 'Her dog found my lost keys.'],
                accepted: [
                    'I thanked the neighbor whose dog found my lost keys.'
                ],
                sampleAnswer: 'I thanked the neighbor whose dog found my lost keys.',
                hint: '把 Her dog 替换成 whose dog，紧跟在 the neighbor 后面。',
                mindMap: {
                    antecedent: 'the neighbor (人)',
                    role: 'Her dog → whose dog（作从句主语）',
                    placement: '紧接 the neighbor 之后',
                    trap: '删掉 her，直接用 whose dog（不可写成 whose her dog）'
                }
            },
            {
                id: 'kp4_q8',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 9',
                prompt: '用 whose 将下面两句话合并为一句（whose 修饰事物）：',
                sentences: ['We read a magazine.', 'Its cover showed a solar eclipse.'],
                accepted: [
                    'We read a magazine whose cover showed a solar eclipse.'
                ],
                sampleAnswer: 'We read a magazine whose cover showed a solar eclipse.',
                hint: 'Its cover → whose cover，直接接在 a magazine 后面。',
                mindMap: {
                    antecedent: 'a magazine (物)',
                    role: 'Its cover → whose cover',
                    placement: 'We read a magazine [whose cover showed a solar eclipse].',
                    trap: 'whose 既可修饰人也可修饰物，不可改用 which cover'
                }
            },
            {
                id: 'kp4_q9',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 10',
                prompt: '用 whose 将下面两句话合并为一句（注意 whose + 名词作从句宾语也不可省略）：',
                sentences: ['The pianist bowed to the audience.', 'We admired his performance.'],
                accepted: [
                    'The pianist whose performance we admired bowed to the audience.'
                ],
                sampleAnswer: 'The pianist whose performance we admired bowed to the audience.',
                hint: '把 his performance 变成 whose performance 提到从句最前面，紧跟 The pianist。',
                mindMap: {
                    antecedent: 'The pianist (人)',
                    role: 'his performance → whose performance（作 admired 宾语）',
                    placement: 'The pianist [whose performance we admired] bowed...',
                    trap: 'whose performance 必须整体提前到 we admired 前面，且删掉 his'
                }
            },
            {
                id: 'kp4_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 11',
                prompt: '用 whose 将下面两句话合并为一句（专有名词 Ms. Alvarez 需加逗号）：',
                sentences: ['Ms. Alvarez teaches environmental science.', 'Her lab won a research grant.'],
                accepted: [
                    'Ms. Alvarez, whose lab won a research grant, teaches environmental science.'
                ],
                sampleAnswer: 'Ms. Alvarez, whose lab won a research grant, teaches environmental science.',
                hint: 'Ms. Alvarez 是人名，用 `, whose lab won a research grant,` 插入主语和 teaches 之间。',
                mindMap: {
                    antecedent: 'Ms. Alvarez (专有名词 · 人)',
                    role: 'Her lab → whose lab',
                    placement: '专有名词后加双逗号：, whose lab won a research grant,',
                    trap: '删掉 Her，并记得保留前后两个逗号'
                }
            }
        ]
    },
    {
        id: 'kp5_where_when',
        number: '05',
        title: '地点与时间 (where / when)',
        subtitle: 'where 替代地点状语 there；when 替代时间状语；警惕 “where + 动词” 的致命陷阱',
        badge: '最易踩坑',
        summary: 'Use where only when you can restate the location with "there". Never use where as the subject of a verb! For time, use when, (that), or Ø.',
        videoScenes: [
            {
                duration: 5000,
                badge: 'Scene 1 · where 的黄金检验法',
                title: '不是看到地点名词就用 where！必须能还原成 “there”',
                leftSentence: 'Chihuahua is the town [where] I was born. (= I was born THERE.) ✅',
                rightSentence: 'Stockholm is a city [where] has beautiful scenery. ❌ (THERE has? 不通！)',
                highlightTarget: 'has beautiful scenery (缺主语)',
                highlightPronoun: 'that / which',
                resultSentence: '✅ Stockholm is a city [that / which] has beautiful scenery.',
                cnTip: '超级口诀：把地点带回从句！需要“在那里 (there)”作地点状语时用 where；本身作主语或宾语时用 which / that！',
                rulePill: 'where = there (地点状语) | where 绝不能作主语'
            },
            {
                duration: 4500,
                badge: 'Scene 2 · where vs Ø 与时间名词 when',
                title: '地点从句句末无介词时必须用 where（不可省略 Ø）',
                leftSentence: '✅ the house [where] my father grew up (= grew up there)',
                rightSentence: '❌ the house [Ø] my father grew up (缺少介词 in！)',
                highlightTarget: 'grew up (后面没有 in)',
                highlightPronoun: 'where (不可用 Ø)',
                resultSentence: '只有写成 "...the house (that/which/Ø) my father grew up IN" 才能用 Ø！',
                cnTip: '时间名词（the day / a time）作状语时比较特殊：when / that / Ø 三者都可以！',
                rulePill: '地点无介词只用 where；时间 when / that / Ø 都行'
            }
        ],
        questions: [
            {
                id: 'kp5_q1',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #2',
                prompt: '选出唯一可以填入括号的正确选项（注意 grew up 后面没有 in）：',
                sentence: 'I was surprised to see the log house ( ______ ) my father grew up.',
                options: ['where', 'which', 'Ø'],
                correctAnswers: ['where'],
                hint: 'my father grew up there (in the log house)。句末没有 in，所以必须用自带地点状语含义的 where，不能单独用 which 或省略 Ø！',
                mindMap: {
                    antecedent: 'the log house (地点)',
                    role: '地点状语 (grew up there)',
                    placement: '句末没有介词 in',
                    trap: '句末缺少介词 in，因此不能单独用 which，也不能省略 Ø，唯一正确答案是 where！'
                }
            },
            {
                id: 'kp5_q2',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #8',
                prompt: '选出唯一正确的选项：',
                sentence: "It's ten miles from the town ( ______ ) I grew up.",
                options: ['when', 'where', 'Ø'],
                correctAnswers: ['where'],
                hint: 'the town 是地点，I grew up THERE（句末没有 in）。',
                mindMap: {
                    antecedent: 'the town (地点)',
                    role: '地点状语 (there)',
                    placement: '限定性从句，无末尾介词',
                    trap: 'when 用于时间；Ø 会导致缺少介词 in'
                }
            },
            {
                id: 'kp5_q3',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #12',
                prompt: '选出所有可以填入括号的正确选项（参考 Step 2 语法表）：',
                sentence: 'I have fond memories of the day ( ______ ) I met my wife.',
                options: ['that', 'when', 'Ø', 'which'],
                correctAnswers: ['that', 'when', 'Ø'],
                hint: 'time 名词（the day）在限定性从句中可以用 when、that，也可以省略 Ø（但不能单独用 which）。',
                mindMap: {
                    antecedent: 'the day (时间)',
                    role: '时间状语 (on that day)',
                    placement: '限定性时间从句',
                    trap: '不能单独用 which 表时间；when / that / Ø 均正确'
                }
            },
            {
                id: 'kp5_q4',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #2',
                prompt: '选出唯一正确的选项：',
                sentence: 'Hong Kong is the city ( ______ ) I was born.',
                options: ['that', 'where', 'which'],
                correctAnswers: ['where'],
                hint: 'I was born there (in Hong Kong)，句末没有 in，所以必须用 where！',
                mindMap: {
                    antecedent: 'the city (地点)',
                    role: '地点状语 (was born there)',
                    placement: '句末无 in',
                    trap: 'that / which 不能单独充当地点状语，必须用 where'
                }
            },
            {
                id: 'kp5_q5',
                type: 'multi',
                sourceTag: 'Packet 4 · Grammar Note 5',
                prompt: '小心“假地点”陷阱！选出所有可以填入括号的正确选项：',
                sentence: 'Stockholm is a city ( ______ ) has beautiful scenery.',
                options: ['where', 'that', 'which'],
                correctAnswers: ['that', 'which'],
                hint: '空格后面直接跟动词 has！所以关系词在从句里作【主语】，不是地点状语（不能说 there has beautiful scenery）。',
                mindMap: {
                    antecedent: 'a city (物/地点名词，但在此作主语)',
                    role: '作从句主语 (It has beautiful scenery)',
                    placement: '主语位置',
                    trap: 'where 只能作状语，绝对不能作主语！'
                }
            },
            {
                id: 'kp5_q6',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #3',
                prompt: '将下面两句话用定语从句合并为一句（注意 My driveway 已被明确限定，通常需逗号）：',
                sentences: ['My driveway is in front of my house.', 'I park four cars there.'],
                accepted: [
                    'My driveway, where I park four cars, is in front of my house.',
                    'My driveway where I park four cars is in front of my house.'
                ],
                sampleAnswer: 'My driveway, where I park four cars, is in front of my house.',
                hint: '用 where 替换句末的 there，并把定语从句放在 My driveway 后面（记得删掉 there！）。',
                mindMap: {
                    antecedent: 'My driveway (特定地点)',
                    role: '地点状语 (there → where)',
                    placement: 'My driveway, [where I park four cars], is in front of my house.',
                    trap: '不要在句末保留 there（❌ where I park four cars there）'
                }
            },
            {
                id: 'kp5_q7',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 12',
                prompt: '用 where 将下面两句话合并为一句（记得删掉句末的 there！）：',
                sentences: ['The quiet cafe closed last month.', 'We used to study there every Sunday.'],
                accepted: [
                    'The quiet cafe where we used to study every Sunday closed last month.'
                ],
                sampleAnswer: 'The quiet cafe where we used to study every Sunday closed last month.',
                hint: '用 where 替换 there，把 where we used to study every Sunday 紧插在 The quiet cafe 后面。',
                mindMap: {
                    antecedent: 'The quiet cafe (地点)',
                    role: '地点状语 (there → where)',
                    placement: 'The quiet cafe [where we used to study every Sunday] closed...',
                    trap: '用 where 替换后必须删掉 there，绝不能写成 where ... study there'
                }
            },
            {
                id: 'kp5_q8',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 13',
                prompt: '用 when（或 that / Ø）将下面两句话合并为一句（删掉 then）：',
                sentences: ['I will never forget the summer.', 'I learned to sail then.'],
                accepted: [
                    'I will never forget the summer when I learned to sail.',
                    'I will never forget the summer that I learned to sail.',
                    'I will never forget the summer I learned to sail.'
                ],
                sampleAnswer: 'I will never forget the summer when I learned to sail.',
                hint: 'the summer 是时间名词，用 when 替换句末的 then（删掉 then）。',
                mindMap: {
                    antecedent: 'the summer (时间)',
                    role: '时间状语 (then → when / that / Ø)',
                    placement: '直接紧跟 the summer 之后',
                    trap: '记得删掉句末多余的 then，也不能单独用 which'
                }
            },
            {
                id: 'kp5_q9',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 14',
                prompt: '小心“假地点”主语陷阱！用正确的关系词合并两句话：',
                sentences: ['Kyoto is a historic city.', 'It attracts millions of travelers each year.'],
                accepted: [
                    'Kyoto is a historic city that attracts millions of travelers each year.',
                    'Kyoto is a historic city which attracts millions of travelers each year.'
                ],
                sampleAnswer: 'Kyoto is a historic city that attracts millions of travelers each year.',
                hint: 'It 在从句中作 attracts 的【主语】，不是地点状语！必须用 that 或 which，不能用 where！',
                mindMap: {
                    antecedent: 'a historic city (作从句主语)',
                    role: 'It → that / which（主语位置）',
                    placement: '紧跟 a historic city 之后',
                    trap: '看到 city 别条件反射写 where！where 绝不能直接加动词 attracts'
                }
            },
            {
                id: 'kp5_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 15',
                prompt: '用 where 将下面两句话合并为一句（专有名词 Northport Harbor 需加逗号）：',
                sentences: ['Northport Harbor is famous for its lighthouse.', 'My grandfather worked there for thirty years.'],
                accepted: [
                    'Northport Harbor, where my grandfather worked for thirty years, is famous for its lighthouse.'
                ],
                sampleAnswer: 'Northport Harbor, where my grandfather worked for thirty years, is famous for its lighthouse.',
                hint: 'Northport Harbor 是专有地名，用 `, where my grandfather worked for thirty years,` 插入主语后，并删掉 there。',
                mindMap: {
                    antecedent: 'Northport Harbor (专有地名)',
                    role: '地点状语 (there → where)',
                    placement: '专有地名后加双逗号：, where my grandfather worked for thirty years,',
                    trap: '必须删掉句末的 there，且前后加逗号'
                }
            }
        ]
    },
    {
        id: 'kp6_commas',
        number: '06',
        title: '限定 vs 非限定从句 (Commas & Traps)',
        subtitle: '有逗号（非限定）的核心铁律：禁用 that、禁用省略 (Ø)；修饰整句话必用 , which',
        badge: '核心区分',
        summary: 'Identifying clauses (no commas) narrow down which noun you mean. Nonidentifying clauses (with commas) add extra info about an already-specific noun — you CANNOT use "that" or omit the pronoun (Ø).',
        videoScenes: [
            {
                duration: 5000,
                badge: 'Scene 1 · 有逗号 vs 无逗号',
                title: '什么时候需要逗号？一看先行词是否已经“独一无二/具体指明”',
                leftSentence: '无逗号（限定性）：The woman who created the test studied psychology.',
                rightSentence: '有逗号（非限定性）：Sara Gomez, who created the test, studied psychology.',
                highlightTarget: 'Sara Gomez / British Petroleum / My new car',
                highlightPronoun: ', who / , which / , whose',
                resultSentence: '专有名词（人名/地名/公司名）或“my + 唯一事物”通常加逗号！',
                cnTip: '逗号就像一对括号，里面的内容是“顺便补充的额外信息”，删掉主句意思依然完整。',
                rulePill: '专有名词 / 唯一事物 → 加逗号（非限定性）'
            },
            {
                duration: 5000,
                badge: 'Scene 2 · 逗号后的两大绝对禁区',
                title: '一旦出现逗号，立刻拉黑 that 和 Ø！',
                leftSentence: '❌ The present, THAT was expensive... / ❌ The present, Ø I bought...',
                rightSentence: '✅ The present, WHICH was expensive... / ✅ Elena, WHOM I met...',
                highlightTarget: '逗号 ( , )',
                highlightPronoun: '禁止 that / 禁止 Ø',
                resultSentence: '💡 补充：修饰整个前面一句话时，也必须用 “, which ...”！',
                cnTip: '例：Boris is detail-oriented, WHICH is why we should hire him.（绝不能用 , that）',
                rulePill: '有逗号 = NO that + NO Ø（仅用 who/whom/which/whose/where/when）'
            }
        ],
        questions: [
            {
                id: 'kp6_q1',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #6',
                prompt: '选出唯一正确的选项（注意 present 后面的逗号！）：',
                sentence: 'I was not expecting the present, ( ______ ) was much too expensive to accept.',
                options: ['that', 'which', 'Ø'],
                correctAnswers: ['which'],
                hint: '注意逗号！非限定性定语从句不能用 that，而且作主语也不能用 Ø。',
                mindMap: {
                    antecedent: 'the present (物)',
                    role: '作从句主语',
                    placement: '逗号后（非限定性定语从句）',
                    trap: '逗号后绝对不能用 that！也不能省略 (Ø)'
                }
            },
            {
                id: 'kp6_q2',
                type: 'multi',
                sourceTag: 'Packet 4 · B8 #9',
                prompt: '选出唯一正确的选项（注意 brother 后面的逗号）：',
                sentence: 'My twin brother, ( ______ ) lives next door, calls me every day.',
                options: ['that', 'who', 'Ø'],
                correctAnswers: ['who'],
                hint: '有逗号的非限定性定语从句指代人时只能用 who（作主语），绝对不能用 that 或 Ø。',
                mindMap: {
                    antecedent: 'My twin brother (人 · 有逗号)',
                    role: '作从句主语 (lives)',
                    placement: '非限定性从句',
                    trap: '逗号后禁止用 that；作主语禁止用 Ø'
                }
            },
            {
                id: 'kp6_q3',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #3',
                prompt: '选出唯一正确的选项（注意 Elena 后面的逗号）：',
                sentence: 'Elena, ( ______ ) I met at the conference, has a Type A personality.',
                options: ['that', 'whom', 'Ø'],
                correctAnswers: ['whom'],
                hint: 'Elena 是人名，后面有逗号（非限定性）！即使作宾语，有逗号时也不能用 that 或 Ø！',
                mindMap: {
                    antecedent: 'Elena (专有名词 · 人 · 有逗号)',
                    role: '作 met 的宾语',
                    placement: '非限定性从句',
                    trap: '平时作宾语可用 that/Ø，但一旦有逗号，that 和 Ø 全部禁用！只能用 whom (或 who)'
                }
            },
            {
                id: 'kp6_q4',
                type: 'multi',
                sourceTag: 'Packet 4 · Review A #5',
                prompt: '选出唯一正确的选项（修饰前面整个句子！）：',
                sentence: 'Boris Popov is very detail-oriented, ( ______ ) is why we should hire him.',
                options: ['that', 'which', 'what'],
                correctAnswers: ['which'],
                hint: '逗号后面指代前面“Boris 非常注重细节”整件事，英语中只能用 which！',
                mindMap: {
                    antecedent: '前面整个分句 (Boris Popov is very detail-oriented)',
                    role: '作主语 (which is why...)',
                    placement: '逗号后非限定性从句',
                    trap: '指代整句话且在逗号后，绝对不能用 that 或 what'
                }
            },
            {
                id: 'kp6_q5',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #4',
                prompt: '将下面两句话合并为一句（专有名词 The Industrial Revolution 需用非限定性逗号）：',
                sentences: ['The Industrial Revolution changed the way people make things.', 'It began in England.'],
                accepted: [
                    'The Industrial Revolution, which began in England, changed the way people make things.'
                ],
                sampleAnswer: 'The Industrial Revolution, which began in England, changed the way people make things.',
                hint: '工业革命是独一无二的专有名词，用 `, which began in England,` 插入在主语后面。',
                mindMap: {
                    antecedent: 'The Industrial Revolution (专有名词 · 物)',
                    role: '作从句主语 (It → which)',
                    placement: '主语后用逗号隔开：, which began in England,',
                    trap: '加逗号后只能用 which，不可写 , that began in England,'
                }
            },
            {
                id: 'kp6_q6',
                type: 'combine',
                sourceTag: 'Packet 4 · Page 10 #6',
                prompt: '将下面两句话合并为一句（注意 British Petroleum 是专有公司名，需要逗号和 which）：',
                sentences: ['British Petroleum received criticism because of the oil spill in the Gulf.', 'It is known as BP.'],
                accepted: [
                    'British Petroleum, which is known as BP, received criticism because of the oil spill in the Gulf.',
                    'British Petroleum, which received criticism because of the oil spill in the Gulf, is known as BP.'
                ],
                sampleAnswer: 'British Petroleum, which is known as BP, received criticism because of the oil spill in the Gulf.',
                hint: 'British Petroleum 是特定公司名，用 `, which is known as BP,` 紧跟在它后面。',
                mindMap: {
                    antecedent: 'British Petroleum (专有名词 · 公司)',
                    role: '作从句主语 (It → which)',
                    placement: 'British Petroleum, [which is known as BP], received...',
                    trap: '专有名词非限定性从句必须用逗号 + which（不可用 that）'
                }
            },
            {
                id: 'kp6_q7',
                type: 'multi',
                sourceTag: 'Packet 4 · Extra Drill 8',
                prompt: '选出唯一正确的选项（注意 Tokyo 后面的逗号）：',
                sentence: 'We flew to Tokyo, ( ______ ) we stayed for five days.',
                options: ['that', 'where', 'Ø', 'which'],
                correctAnswers: ['where'],
                hint: 'Tokyo 是专有地名且后面有逗号（非限定性），stayed there 需要地点状语，只能选 where！',
                mindMap: {
                    antecedent: 'Tokyo (专有地名 · 有逗号)',
                    role: '地点状语 (stayed there)',
                    placement: '逗号后非限定性地点从句',
                    trap: '逗号后禁用 that 和 Ø；单独 which 缺少介词 in，唯一正确是 where'
                }
            },
            {
                id: 'kp6_q8',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 16',
                prompt: '将下面两句话合并为一句（专有名词 Dr. Lin 需用逗号和非限定性 who）：',
                sentences: ['Dr. Lin founded the robotics club.', 'She advises our senior team.'],
                accepted: [
                    'Dr. Lin, who advises our senior team, founded the robotics club.',
                    'Dr. Lin, who founded the robotics club, advises our senior team.'
                ],
                sampleAnswer: 'Dr. Lin, who advises our senior team, founded the robotics club.',
                hint: 'Dr. Lin 是人名（专有名词），加双逗号并用 who 替换 She（绝对不能用 that！）。',
                mindMap: {
                    antecedent: 'Dr. Lin (专有名词 · 人)',
                    role: '作从句主语 (She → who)',
                    placement: 'Dr. Lin, [who advises our senior team], founded...',
                    trap: '有逗号时绝对禁用 that（❌ Dr. Lin, that advises...）'
                }
            },
            {
                id: 'kp6_q9',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 17',
                prompt: '将下面两句话合并为一句（用 , which 指代前面整件事！）：',
                sentences: ['The bus arrived thirty minutes late.', 'This caused us to miss the opening speech.'],
                accepted: [
                    'The bus arrived thirty minutes late, which caused us to miss the opening speech.'
                ],
                sampleAnswer: 'The bus arrived thirty minutes late, which caused us to miss the opening speech.',
                hint: 'This 指代前面整句话，在逗号后面把 This 换成 which！',
                mindMap: {
                    antecedent: '前面整个分句 (The bus arrived thirty minutes late)',
                    role: '指代整件事作主语 (This → , which)',
                    placement: '紧跟前句逗号之后：, which caused us...',
                    trap: '修饰整句话只能用 , which，绝不能用 , that 或 , what'
                }
            },
            {
                id: 'kp6_q10',
                type: 'combine',
                sourceTag: 'Packet 4 · Extra Combine 18',
                prompt: '将下面两句话合并为一句（专有名词 Mount Fuji 需用逗号和 which）：',
                sentences: ['Mount Fuji appears in many woodblock prints.', 'It rises above the surrounding plains.'],
                accepted: [
                    'Mount Fuji, which rises above the surrounding plains, appears in many woodblock prints.',
                    'Mount Fuji, which appears in many woodblock prints, rises above the surrounding plains.'
                ],
                sampleAnswer: 'Mount Fuji, which rises above the surrounding plains, appears in many woodblock prints.',
                hint: 'Mount Fuji 是独一无二的专有名词，用 `, which ... ,` 插入主语后（禁用 that）。',
                mindMap: {
                    antecedent: 'Mount Fuji (专有名词 · 物)',
                    role: '作从句主语 (It → which)',
                    placement: 'Mount Fuji, [which rises above the surrounding plains], appears...',
                    trap: '逗号后面必须用 which，绝不能用 that'
                }
            }
        ]
    }
];

window.GRAMMAR_TOPICS = GRAMMAR_TOPICS;
