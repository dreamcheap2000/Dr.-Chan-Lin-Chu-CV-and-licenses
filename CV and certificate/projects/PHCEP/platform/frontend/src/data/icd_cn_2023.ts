/**
 * Chinese ICD-10 2023 — Phase 1 code set
 *
 * Scope: Neurology (G), Cerebrovascular disease (I60–I69),
 *        Cardiovascular (I20–I25, I48, I10–I13), Epilepsy (G40–G41),
 *        Migraine/Headache (G43–G44), Dementia (F00–F03, G30),
 *        Parkinson/Movement (G20–G26), TIA (G45–G46),
 *        Sleep disorders (G47), Head injury (S06).
 *
 * Phase 2 (next session): full Chapter I Circulatory + Chapter J Respiratory.
 *
 * Format: { code, cn, en }
 *   cn = Chinese description (2023 National Standard)
 *   en = English description
 */

export interface IcdEntry {
  code: string;
  cn: string;
  en: string;
}

/** Full label for autocomplete dropdown: "CODE 中文名稱（English）" */
export function icdLabel(e: IcdEntry): string {
  return `${e.code} ${e.cn}（${e.en}）`;
}

/** Short label inserted into fields: "CODE 中文名稱" */
export function icdShortLabel(e: IcdEntry): string {
  return `${e.code} ${e.cn}`;
}

const ICD_CN_2023: IcdEntry[] = [
  // ── 蜘蛛膜下腔出血 ─────────────────────────────────────────────────────────
  { code: 'I60',   cn: '蜘蛛膜下腔出血',                   en: 'Subarachnoid haemorrhage' },
  { code: 'I60.0', cn: '頸動脈竇及分叉部蜘蛛膜下腔出血',    en: 'SAH from carotid siphon and bifurcation' },
  { code: 'I60.1', cn: '中大腦動脈蜘蛛膜下腔出血',          en: 'SAH from middle cerebral artery' },
  { code: 'I60.2', cn: '前交通動脈蜘蛛膜下腔出血',          en: 'SAH from anterior communicating artery' },
  { code: 'I60.3', cn: '後交通動脈蜘蛛膜下腔出血',          en: 'SAH from posterior communicating artery' },
  { code: 'I60.4', cn: '基底動脈蜘蛛膜下腔出血',            en: 'SAH from basilar artery' },
  { code: 'I60.5', cn: '椎動脈蜘蛛膜下腔出血',              en: 'SAH from vertebral artery' },
  { code: 'I60.9', cn: '蜘蛛膜下腔出血，未特定',            en: 'Subarachnoid haemorrhage, unspecified' },
  // ── 腦內出血 ──────────────────────────────────────────────────────────────
  { code: 'I61',   cn: '腦內出血',                          en: 'Intracerebral haemorrhage' },
  { code: 'I61.0', cn: '半球皮質下腦內出血',                en: 'Intracerebral haemorrhage in hemisphere, subcortical' },
  { code: 'I61.1', cn: '半球皮質腦內出血',                  en: 'Intracerebral haemorrhage in hemisphere, cortical' },
  { code: 'I61.2', cn: '半球腦內出血，未特定',              en: 'Intracerebral haemorrhage in hemisphere, unspecified' },
  { code: 'I61.3', cn: '腦幹腦內出血',                      en: 'Intracerebral haemorrhage in brain stem' },
  { code: 'I61.4', cn: '小腦腦內出血',                      en: 'Intracerebral haemorrhage in cerebellum' },
  { code: 'I61.5', cn: '腦室內出血',                        en: 'Intracerebral haemorrhage, intraventricular' },
  { code: 'I61.6', cn: '多部位腦內出血',                    en: 'Intracerebral haemorrhage, multiple localized' },
  { code: 'I61.9', cn: '腦內出血，未特定',                  en: 'Intracerebral haemorrhage, unspecified' },
  // ── 其他顱內出血 ──────────────────────────────────────────────────────────
  { code: 'I62',   cn: '其他非創傷性顱內出血',              en: 'Other nontraumatic intracranial haemorrhage' },
  { code: 'I62.0', cn: '硬膜下出血（急性）（非創傷性）',    en: 'Subdural haemorrhage (acute)(nontraumatic)' },
  { code: 'I62.1', cn: '非創傷性硬膜外出血',                en: 'Nontraumatic extradural haemorrhage' },
  { code: 'I62.9', cn: '顱內出血，未特定',                  en: 'Intracranial haemorrhage, unspecified' },
  // ── 腦梗塞 ────────────────────────────────────────────────────────────────
  { code: 'I63',   cn: '腦梗塞',                            en: 'Cerebral infarction' },
  { code: 'I63.0', cn: '腦前動脈血栓形成所致腦梗塞',        en: 'Cerebral infarction due to thrombosis of precerebral arteries' },
  { code: 'I63.1', cn: '腦前動脈栓塞所致腦梗塞',            en: 'Cerebral infarction due to embolism of precerebral arteries' },
  { code: 'I63.2', cn: '腦前動脈未特定閉塞所致腦梗塞',      en: 'Cerebral infarction due to unspecified occlusion of precerebral arteries' },
  { code: 'I63.3', cn: '腦動脈血栓形成所致腦梗塞',          en: 'Cerebral infarction due to thrombosis of cerebral arteries' },
  { code: 'I63.4', cn: '腦動脈栓塞所致腦梗塞',              en: 'Cerebral infarction due to embolism of cerebral arteries' },
  { code: 'I63.5', cn: '腦動脈未特定閉塞所致腦梗塞',        en: 'Cerebral infarction due to unspecified occlusion of cerebral arteries' },
  { code: 'I63.6', cn: '腦靜脈血栓形成所致腦梗塞',          en: 'Cerebral infarction due to cerebral venous thrombosis' },
  { code: 'I63.8', cn: '其他腦梗塞',                        en: 'Other cerebral infarction' },
  { code: 'I63.9', cn: '腦梗塞，未特定',                    en: 'Cerebral infarction, unspecified' },
  { code: 'I64',   cn: '腦中風，未特定出血性或梗塞性',       en: 'Stroke, not specified as haemorrhage or infarction' },
  // ── 腦前動脈閉塞及狹窄 ───────────────────────────────────────────────────
  { code: 'I65',   cn: '腦前動脈閉塞及狹窄，未造成腦梗塞',  en: 'Occlusion and stenosis of precerebral arteries' },
  { code: 'I65.0', cn: '椎動脈閉塞及狹窄',                  en: 'Occlusion and stenosis of vertebral artery' },
  { code: 'I65.1', cn: '基底動脈閉塞及狹窄',                en: 'Occlusion and stenosis of basilar artery' },
  { code: 'I65.2', cn: '頸動脈閉塞及狹窄',                  en: 'Occlusion and stenosis of carotid artery' },
  { code: 'I65.3', cn: '多發性及雙側腦前動脈閉塞及狹窄',    en: 'Occlusion and stenosis of multiple/bilateral precerebral arteries' },
  { code: 'I65.9', cn: '腦前動脈閉塞及狹窄，未特定',        en: 'Occlusion and stenosis of precerebral artery, unspecified' },
  // ── 腦動脈閉塞及狹窄 ─────────────────────────────────────────────────────
  { code: 'I66',   cn: '腦動脈閉塞及狹窄，未造成腦梗塞',    en: 'Occlusion and stenosis of cerebral arteries' },
  { code: 'I66.0', cn: '大腦中動脈閉塞及狹窄',              en: 'Occlusion and stenosis of middle cerebral artery' },
  { code: 'I66.1', cn: '大腦前動脈閉塞及狹窄',              en: 'Occlusion and stenosis of anterior cerebral artery' },
  { code: 'I66.2', cn: '大腦後動脈閉塞及狹窄',              en: 'Occlusion and stenosis of posterior cerebral artery' },
  { code: 'I66.3', cn: '小腦動脈閉塞及狹窄',                en: 'Occlusion and stenosis of cerebellar arteries' },
  { code: 'I66.9', cn: '腦動脈閉塞及狹窄，未特定',          en: 'Occlusion and stenosis of cerebral artery, unspecified' },
  // ── 其他腦血管疾病 ────────────────────────────────────────────────────────
  { code: 'I67',   cn: '其他腦血管疾病',                    en: 'Other cerebrovascular diseases' },
  { code: 'I67.0', cn: '腦動脈剝離',                        en: 'Dissection of cerebral arteries, nonruptured' },
  { code: 'I67.1', cn: '腦動脈瘤（未破裂）',                en: 'Cerebral aneurysm, nonruptured' },
  { code: 'I67.2', cn: '腦動脈硬化',                        en: 'Cerebral atherosclerosis' },
  { code: 'I67.3', cn: '進行性血管性白質腦病',              en: 'Progressive vascular leukoencephalopathy' },
  { code: 'I67.4', cn: '高血壓性腦病',                      en: 'Hypertensive encephalopathy' },
  { code: 'I67.5', cn: '煙霧病',                            en: 'Moyamoya disease' },
  { code: 'I67.6', cn: '非化膿性顱內靜脈系統血栓形成',      en: 'Nonpyogenic thrombosis of intracranial venous system' },
  { code: 'I67.7', cn: '腦動脈炎',                          en: 'Cerebral arteritis' },
  { code: 'I67.8', cn: '其他特定腦血管疾病',                en: 'Other specified cerebrovascular diseases' },
  { code: 'I67.9', cn: '腦血管疾病，未特定',                en: 'Cerebrovascular disease, unspecified' },
  { code: 'I69',   cn: '腦血管疾病後遺症',                  en: 'Sequelae of cerebrovascular disease' },
  { code: 'I69.0', cn: '蜘蛛膜下腔出血後遺症',              en: 'Sequelae of subarachnoid haemorrhage' },
  { code: 'I69.1', cn: '腦內出血後遺症',                    en: 'Sequelae of intracerebral haemorrhage' },
  { code: 'I69.3', cn: '腦梗塞後遺症',                      en: 'Sequelae of cerebral infarction' },
  { code: 'I69.4', cn: '中風後遺症，未特定',                en: 'Sequelae of stroke, not specified as haemorrhage or infarction' },
  // ── 高血壓 ────────────────────────────────────────────────────────────────
  { code: 'I10',   cn: '原發性（特發性）高血壓',            en: 'Essential (primary) hypertension' },
  { code: 'I11',   cn: '高血壓性心臟病',                    en: 'Hypertensive heart disease' },
  { code: 'I12',   cn: '高血壓性腎臟病',                    en: 'Hypertensive renal disease' },
  { code: 'I13',   cn: '高血壓性心臟及腎臟病',              en: 'Hypertensive heart and renal disease' },
  // ── 心絞痛及急性心肌梗塞 ─────────────────────────────────────────────────
  { code: 'I20',   cn: '心絞痛',                            en: 'Angina pectoris' },
  { code: 'I20.0', cn: '不穩定心絞痛',                      en: 'Unstable angina' },
  { code: 'I20.1', cn: '有記錄血管痙攣之心絞痛',            en: 'Angina pectoris with documented spasm' },
  { code: 'I20.9', cn: '心絞痛，未特定',                    en: 'Angina pectoris, unspecified' },
  { code: 'I21',   cn: '急性心肌梗塞',                      en: 'Acute myocardial infarction' },
  { code: 'I21.0', cn: '前壁急性透壁性心肌梗塞',            en: 'Acute transmural MI of anterior wall' },
  { code: 'I21.1', cn: '下壁急性透壁性心肌梗塞',            en: 'Acute transmural MI of inferior wall' },
  { code: 'I21.2', cn: '其他部位急性透壁性心肌梗塞',        en: 'Acute transmural MI of other sites' },
  { code: 'I21.3', cn: '急性透壁性心肌梗塞，未特定部位',    en: 'Acute transmural MI of unspecified site' },
  { code: 'I21.4', cn: '急性心內膜下心肌梗塞',              en: 'Acute subendocardial myocardial infarction' },
  { code: 'I21.9', cn: '急性心肌梗塞，未特定',              en: 'Acute myocardial infarction, unspecified' },
  { code: 'I25',   cn: '慢性缺血性心臟病',                  en: 'Chronic ischaemic heart disease' },
  { code: 'I25.1', cn: '動脈硬化性心臟病',                  en: 'Atherosclerotic heart disease' },
  { code: 'I25.2', cn: '陳舊性心肌梗塞',                    en: 'Old myocardial infarction' },
  // ── 心房顫動 ──────────────────────────────────────────────────────────────
  { code: 'I48',   cn: '心房顫動及心房撲動',                en: 'Atrial fibrillation and flutter' },
  { code: 'I48.0', cn: '陣發性心房顫動',                    en: 'Paroxysmal atrial fibrillation' },
  { code: 'I48.1', cn: '持續性心房顫動',                    en: 'Persistent atrial fibrillation' },
  { code: 'I48.2', cn: '慢性心房顫動',                      en: 'Chronic atrial fibrillation' },
  { code: 'I48.9', cn: '心房顫動及心房撲動，未特定',        en: 'Atrial fibrillation and flutter, unspecified' },
  // ── 癲癇 ─────────────────────────────────────────────────────────────────
  { code: 'G40',   cn: '癲癇',                              en: 'Epilepsy' },
  { code: 'G40.0', cn: '局部（局灶）特發性癲癇',            en: 'Localization-related idiopathic epilepsy' },
  { code: 'G40.1', cn: '局部（局灶）症狀性癲癇（簡單部分型）', en: 'Localization-related symptomatic epilepsy (simple partial)' },
  { code: 'G40.2', cn: '局部（局灶）症狀性癲癇（複雜部分型）', en: 'Localization-related symptomatic epilepsy (complex partial)' },
  { code: 'G40.3', cn: '全身性特發性癲癇及癲癇症候群',      en: 'Generalized idiopathic epilepsy and epileptic syndromes' },
  { code: 'G40.4', cn: '其他全身性癲癇及癲癇症候群',        en: 'Other generalized epilepsy and epileptic syndromes' },
  { code: 'G40.5', cn: '特定癲癇症候群',                    en: 'Special epileptic syndromes' },
  { code: 'G40.6', cn: '大發作，未特定',                    en: 'Grand mal seizures, unspecified' },
  { code: 'G40.7', cn: '小發作，未特定',                    en: 'Petit mal, unspecified' },
  { code: 'G40.8', cn: '其他癲癇',                          en: 'Other epilepsy' },
  { code: 'G40.9', cn: '癲癇，未特定',                      en: 'Epilepsy, unspecified' },
  { code: 'G41',   cn: '癲癇持續狀態',                      en: 'Status epilepticus' },
  { code: 'G41.0', cn: '強直陣攣型癲癇持續狀態',            en: 'Grand mal status epilepticus' },
  { code: 'G41.1', cn: '小發作型癲癇持續狀態',              en: 'Petit mal status epilepticus' },
  { code: 'G41.2', cn: '複雜部分型癲癇持續狀態',            en: 'Complex partial status epilepticus' },
  { code: 'G41.9', cn: '癲癇持續狀態，未特定',              en: 'Status epilepticus, unspecified' },
  // ── 偏頭痛與頭痛 ─────────────────────────────────────────────────────────
  { code: 'G43',   cn: '偏頭痛',                            en: 'Migraine' },
  { code: 'G43.0', cn: '無先兆偏頭痛',                      en: 'Migraine without aura (common migraine)' },
  { code: 'G43.1', cn: '有先兆偏頭痛',                      en: 'Migraine with aura (classical migraine)' },
  { code: 'G43.2', cn: '偏頭痛持續狀態',                    en: 'Status migrainosus' },
  { code: 'G43.3', cn: '複雜性偏頭痛',                      en: 'Complicated migraine' },
  { code: 'G43.8', cn: '其他偏頭痛',                        en: 'Other migraine' },
  { code: 'G43.9', cn: '偏頭痛，未特定',                    en: 'Migraine, unspecified' },
  { code: 'G44',   cn: '其他頭痛症候群',                    en: 'Other headache syndromes' },
  { code: 'G44.0', cn: '叢發性頭痛症候群',                  en: 'Cluster headache syndrome' },
  { code: 'G44.1', cn: '血管性頭痛，未他處分類',            en: 'Vascular headache, not elsewhere classified' },
  { code: 'G44.2', cn: '緊縮型頭痛',                        en: 'Tension-type headache' },
  { code: 'G44.3', cn: '慢性創傷後頭痛',                    en: 'Chronic post-traumatic headache' },
  { code: 'G44.4', cn: '藥物誘導性頭痛，未他處分類',        en: 'Drug-induced headache, not elsewhere classified' },
  // ── 帕金森症及運動疾患 ───────────────────────────────────────────────────
  { code: 'G20',   cn: '帕金森病',                          en: 'Parkinson disease' },
  { code: 'G21',   cn: '繼發性帕金森症',                    en: 'Secondary parkinsonism' },
  { code: 'G21.0', cn: '惡性神經阻滯劑症候群',              en: 'Malignant neuroleptic syndrome' },
  { code: 'G21.1', cn: '其他藥物誘導性繼發性帕金森症',      en: 'Other drug-induced secondary parkinsonism' },
  { code: 'G21.3', cn: '腦炎後帕金森症',                    en: 'Postencephalitic parkinsonism' },
  { code: 'G22',   cn: '帕金森症（見於他處分類疾病）',      en: 'Parkinsonism in diseases classified elsewhere' },
  { code: 'G23',   cn: '基底核其他退化性疾病',              en: 'Other degenerative diseases of basal ganglia' },
  { code: 'G24',   cn: '肌張力不全',                        en: 'Dystonia' },
  { code: 'G25',   cn: '其他錐體外徑及運動疾患',            en: 'Other extrapyramidal and movement disorders' },
  { code: 'G25.0', cn: '原發性震顫',                        en: 'Essential tremor' },
  // ── 失智症 ────────────────────────────────────────────────────────────────
  { code: 'F00',   cn: '阿茲海默症失智',                    en: 'Dementia in Alzheimer disease' },
  { code: 'F00.0', cn: '早發型阿茲海默症失智',              en: 'Dementia in Alzheimer disease with early onset' },
  { code: 'F00.1', cn: '晚發型阿茲海默症失智',              en: 'Dementia in Alzheimer disease with late onset' },
  { code: 'F00.2', cn: '阿茲海默症失智，非典型或混合型',    en: 'Dementia in Alzheimer disease, atypical or mixed type' },
  { code: 'F01',   cn: '血管性失智',                        en: 'Vascular dementia' },
  { code: 'F01.0', cn: '急性發作性血管性失智',              en: 'Vascular dementia of acute onset' },
  { code: 'F01.1', cn: '多發梗塞性失智',                    en: 'Multi-infarct dementia' },
  { code: 'F01.2', cn: '皮質下血管性失智',                  en: 'Subcortical vascular dementia' },
  { code: 'F01.3', cn: '皮質及皮質下混合性血管性失智',      en: 'Mixed cortical and subcortical vascular dementia' },
  { code: 'F02',   cn: '其他疾病引起之失智',                en: 'Dementia in other diseases classified elsewhere' },
  { code: 'F03',   cn: '失智症，未特定',                    en: 'Unspecified dementia' },
  { code: 'G30',   cn: '阿茲海默症',                        en: 'Alzheimer disease' },
  { code: 'G30.0', cn: '早發型阿茲海默症',                  en: 'Alzheimer disease with early onset' },
  { code: 'G30.1', cn: '晚發型阿茲海默症',                  en: 'Alzheimer disease with late onset' },
  { code: 'G30.8', cn: '其他阿茲海默症',                    en: 'Other Alzheimer disease' },
  { code: 'G30.9', cn: '阿茲海默症，未特定',                en: 'Alzheimer disease, unspecified' },
  // ── 週邊神經病變 ──────────────────────────────────────────────────────────
  { code: 'G50',   cn: '三叉神經疾患',                      en: 'Disorders of trigeminal nerve' },
  { code: 'G51',   cn: '顏面神經疾患',                      en: 'Facial nerve disorders' },
  { code: 'G51.0', cn: '貝爾氏麻痺',                        en: "Bell's palsy" },
  { code: 'G54',   cn: '神經根及神經叢疾患',                en: 'Nerve root and plexus disorders' },
  { code: 'G54.2', cn: '頸神經根病',                        en: 'Cervical root disorders, NEC' },
  { code: 'G54.3', cn: '胸神經根病',                        en: 'Thoracic root disorders, NEC' },
  { code: 'G54.4', cn: '腰薦神經根病',                      en: 'Lumbosacral root disorders, NEC' },
  { code: 'G61',   cn: '發炎性多發神經病',                  en: 'Inflammatory polyneuropathy' },
  { code: 'G61.0', cn: '吉巴症候群',                        en: 'Guillain-Barré syndrome' },
  { code: 'G62',   cn: '其他多發神經病',                    en: 'Other polyneuropathies' },
  { code: 'G62.0', cn: '藥物誘導性多發神經病',              en: 'Drug-induced polyneuropathy' },
  { code: 'G62.1', cn: '酒精誘導性多發神經病',              en: 'Alcoholic polyneuropathy' },
  // ── 脫髓鞘疾病 ───────────────────────────────────────────────────────────
  { code: 'G35',   cn: '多發性硬化症',                      en: 'Multiple sclerosis' },
  { code: 'G36',   cn: '其他急性散播性脫髓鞘',              en: 'Other acute disseminated demyelination' },
  // ── TIA ──────────────────────────────────────────────────────────────────
  { code: 'G45',   cn: '短暫性腦缺血發作及相關症候群',      en: 'Transient cerebral ischaemic attacks and related syndromes' },
  { code: 'G45.0', cn: '椎基底動脈症候群',                  en: 'Vertebro-basilar artery syndrome' },
  { code: 'G45.1', cn: '頸動脈症候群（半球性）',            en: 'Carotid artery syndrome (hemispheric)' },
  { code: 'G45.3', cn: '黑矇性短暫失明',                    en: 'Amaurosis fugax' },
  { code: 'G45.4', cn: '短暫性整體性失憶',                  en: 'Transient global amnesia' },
  { code: 'G45.9', cn: '短暫性腦缺血發作，未特定',          en: 'Transient cerebral ischaemic attack, unspecified' },
  { code: 'G46',   cn: '腦血管疾病之腦血管症候群',          en: 'Vascular syndromes of brain in cerebrovascular diseases' },
  // ── 睡眠疾患 ─────────────────────────────────────────────────────────────
  { code: 'G47',   cn: '睡眠疾患',                          en: 'Sleep disorders' },
  { code: 'G47.0', cn: '入眠及維持睡眠困難（失眠）',        en: 'Disorders of initiating and maintaining sleep (insomnias)' },
  { code: 'G47.3', cn: '睡眠呼吸中止',                      en: 'Sleep apnoea' },
  { code: 'G47.4', cn: '猝睡症及猝倒症',                    en: 'Narcolepsy and cataplexy' },
  // ── 頭部外傷 ──────────────────────────────────────────────────────────────
  { code: 'S06',   cn: '顱內損傷',                          en: 'Intracranial injury' },
  { code: 'S06.0', cn: '腦震盪',                            en: 'Concussion' },
  { code: 'S06.1', cn: '創傷性腦水腫',                      en: 'Traumatic cerebral oedema' },
  { code: 'S06.2', cn: '瀰漫性腦損傷',                      en: 'Diffuse brain injury' },
  { code: 'S06.3', cn: '局部性腦損傷',                      en: 'Focal brain injury' },
  { code: 'S06.4', cn: '硬膜外出血',                        en: 'Epidural haemorrhage' },
  { code: 'S06.5', cn: '創傷性硬膜下出血',                  en: 'Traumatic subdural haemorrhage' },
  { code: 'S06.6', cn: '創傷性蜘蛛膜下腔出血',              en: 'Traumatic subarachnoid haemorrhage' },
];

export default ICD_CN_2023;
