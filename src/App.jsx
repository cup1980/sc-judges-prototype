import { useState, useRef, useEffect } from "react";

// =====================
// データ
// =====================
// field … 集計用の正規化分野（マトリクスはこれを使う）
// topic … 表示用の自由記述（カード等で使う）
const NOTABLE_OPINIONS = [
  {
    id: "miura-genpatsu",
    judgeId: "miura",
    judgeName: "三浦 守",
    judgeBackground: "検察官",
    date: "2022年6月17日",
    court: "最高裁判所 第二小法廷",
    caseName: "原発賠償訴訟（国の規制権限不行使）",
    caseNumber: "",
    opinionType: "反対意見",
    topic: "原発・国家賠償",
    field: "行政",
    topicColor: "#dc4a26",
    hanreiUrl: "https://www.courts.go.jp/hanrei/91243/detail2/index.html",
    outcome: "国の賠償責任を否定（上告棄却）",
    outcomeKind: "棄却",
    aiSummary: "津波による福島原発事故をめぐり、国の規制権限不行使に国家賠償責任はないとした多数意見に対して、三浦判事は単独で反対した。検察官出身の三浦判事が被害者側を支持するという構図が注目を集めた。",
    background: "2011年東日本大震災による福島第一原発事故。避難を余儀なくされた住民らが「国は津波の危険性を予見できたのに規制権限を行使しなかった」として国に損害賠償を求めた。",
    majority: "多数意見（3名）は「仮に規制権限を行使して防潮堤を造っていたとしても、実際の津波規模が試算を大幅に超えていたため事故は防げなかった（結果回避可能性なし）」として国の賠償責任を否定した。",
    dissent: "三浦判事は、津波の予見可能性と回避可能性を詳細に検討し、国が適切な規制権限を行使すれば事故を防げた可能性があると判断。「津波高の試算の合理性」「防潮堤以外の対策の可能性」などを丁寧に論じ、国の責任を認めるべきと主張した。",
    significance: "最高裁が同日に4件の原発賠償訴訟を判決し、いずれも国の責任を否定した中で、三浦判事の反対意見だけが国の責任を認めた。法曹界では「珠玉の意見」と評価する声もあった。",
    quote: "経済産業大臣が規制権限を行使して…適切な措置を講ずることを義務付けていれば、本件原子力事故…が発生しなかったであろうという関係を認めることができる",
  },
  {
    id: "miura-fuufu",
    judgeId: "miura",
    judgeName: "三浦 守",
    judgeBackground: "検察官",
    date: "2021年6月23日",
    court: "最高裁判所 大法廷",
    caseName: "夫婦別姓訴訟（夫婦同氏制の合憲性）",
    caseNumber: "令和2(ク)102",
    opinionType: "意見（違憲寄り）",
    topic: "ジェンダー・家族法",
    field: "家族法",
    topicColor: "#7c3aed",
    hanreiUrl: "https://www.courts.go.jp/hanrei/90039/detail2/index.html",
    outcome: "夫婦同氏制は合憲",
    outcomeKind: "合憲",
    aiSummary: "夫婦同姓を義務付ける民法規定を合憲とした大法廷決定で、三浦判事は多数意見に加わらず独自の「意見」を付した。婚姻の自由が憲法24条1項で保障されると解し、現行制度は実質的に婚姻の自由を侵害するという違憲寄りの立場をとった。",
    background: "民法750条は「夫婦は、婚姻の際に定めるところに従い、夫又は妻の氏を称する」と規定。実態として96%の夫婦が夫の姓を選んでおり、選択的夫婦別姓の法制化を求める声が根強い。",
    majority: "多数意見（11名）は夫婦同氏制を合憲と判断。「どちらの姓を選ぶかは夫婦の協議で決められる」「旧姓の通称使用により一定の緩和ができる」として合憲とし、制度変更は国会の判断に委ねるとした。",
    dissent: "三浦判事は「婚姻をするについての意思決定と同時に、人格的利益の喪失を受け入れる意思決定を求めることであるから、婚姻についての意思決定が自由かつ平等であるとは到底いえない」と述べ、夫婦同氏強制は婚姻の自由を侵害すると主張。女性3判事の反対意見とは異なる独自の論理構成で違憲に近い立場をとった。",
    significance: "大法廷15名中、宮崎裕子・宇賀克也の2名が「反対意見」（違憲）、三浦守が「意見」（違憲寄り）、計3名が現行制度に否定的な見解を示した。検察官出身の三浦判事が人格権・ジェンダー平等の観点から論じた点が注目された。",
    quote: "婚姻の際に氏の変更を望まない当事者にとって、その氏の維持に係る人格的利益は、婚姻という選択と引き換えにその喪失を甘受しなければならないものではない",
  },
  {
    id: "miura-sei",
    judgeId: "miura",
    judgeName: "三浦 守",
    judgeBackground: "検察官",
    date: "2023年10月25日",
    court: "最高裁判所 大法廷",
    caseName: "性同一性障害特例法・生殖不能要件違憲決定",
    caseNumber: "",
    opinionType: "反対意見",
    topic: "性的少数者の権利",
    field: "憲法・人権",
    topicColor: "#0891b2",
    hanreiUrl: "https://www.courts.go.jp/hanrei/92527/detail2/index.html",
    outcome: "生殖不能要件は違憲・無効",
    outcomeKind: "違憲",
    aiSummary: "性別変更に「生殖不能手術」を要件とする性同一性障害特例法の規定を、大法廷が全員一致で違憲・無効とした。三浦判事は結論（違憲）には賛成しつつ、多数意見の判断手法に異議を唱える反対意見を付した。",
    background: "性同一性障害特例法3条1項4号は、性別変更の要件として「生殖腺がないこと又は生殖腺の機能を永続的に欠く状態にあること」を定めていた。不妊手術の強制を伴うこの要件は国際的にも問題視されていた。",
    majority: "大法廷は全員一致で当該要件を憲法13条（幸福追求権）に違反すると判断。身体への侵襲を強制することは「意思に反して身体への侵襲を受けない自由」を侵害するとした。",
    dissent: "三浦判事は違憲の結論自体には賛同しつつ、「多数意見は当該要件の趣旨・目的の検討が不十分」と批判。要件の立法目的を十分に吟味した上で違憲と判断すべきという、異なる理由付けを主張した。判断の丁寧さに関する方法論的な異議といえる。",
    significance: "全員一致の画期的な違憲判断の中で、三浦判事だけが「なぜ違憲か」の論理に異議を唱えた。少数意見が「方向性は同じだが理由が違う」という珍しい形の個別意見で、裁判官が判断手法にも強いこだわりを持つことを示した。",
    quote: "当該要件が設けられた趣旨・目的を十分に検討した上で、その目的の重要性と手段の相当性について判断すべきである",
  },
  {
    id: "hayashi-ikka",
    judgeId: "hayashi",
    judgeName: "林 道晴",
    judgeBackground: "裁判官",
    date: "2022年5月25日",
    court: "最高裁判所 大法廷",
    caseName: "在外国民国民審査権確認訴訟",
    caseNumber: "",
    opinionType: "多数意見（全員一致）",
    topic: "選挙・民主主義",
    field: "選挙・民主主義",
    topicColor: "#16a34a",
    hanreiUrl: "https://www.courts.go.jp/hanrei/91190/detail2/index.html",
    outcome: "在外国民の審査権制限は違憲",
    outcomeKind: "違憲",
    aiSummary: "海外に住む日本人が最高裁裁判官の国民審査に投票できない制度を、大法廷が全員一致で違憲と判断した画期的な判決。林判事も多数意見に加わった。この判決を受けて法改正が行われ、2024年の国民審査から在外投票が実現した。",
    background: "在外邦人は衆議院・参議院選挙への投票は認められていたが、最高裁裁判官の国民審査の投票権は認められていなかった。この不均衡に対して在外邦人が訴訟を提起した。",
    majority: "大法廷は全員一致で、在外国民に国民審査権の行使を認めない現行法は憲法15条1項・79条2項・3項に違反すると判断。審査権は選挙権と並ぶ重要な民主的コントロール手段であり、合理的理由なく制限できないとした。",
    dissent: "全員一致のため個別意見なし。",
    significance: "この判決を受けて国民審査法が改正され、2024年10月の衆院選と同時の国民審査から在外投票・洋上投票が実現した。まさに司法が民主主義を前進させた事例といえる。",
    quote: "在外国民は、衆議院議員の選挙については投票をすることが認められているにもかかわらず、審査については投票をすることが認められていない合理的な理由は見当たらない",
  },
  {
    id: "uga-fuufu",
    judgeId: "uga",
    judgeName: "宇賀 克也",
    judgeBackground: "学者",
    date: "2021年6月23日",
    court: "最高裁判所 大法廷",
    caseName: "夫婦別姓訴訟（夫婦同氏制の合憲性）",
    caseNumber: "令和2(ク)102",
    opinionType: "反対意見",
    topic: "ジェンダー・家族法",
    field: "家族法",
    topicColor: "#7c3aed",
    hanreiUrl: "https://www.courts.go.jp/hanrei/90039/detail2/index.html",
    outcome: "夫婦同氏制は合憲",
    outcomeKind: "合憲",
    aiSummary: "夫婦同姓を合憲とした大法廷決定で、宇賀判事は宮崎裕子判事とともに「違憲」とする反対意見を付した。行政法学者出身の宇賀判事は、夫婦同姓の強制が自由かつ平等な意思決定を妨げ、憲法24条の趣旨に反すると論じた。",
    background: "夫婦別姓を記載した婚姻届が不受理とされたことを不服として起こされた裁判の抗告審。民法750条が憲法に違反するかが争われた。",
    majority: "大法廷は15名中11名の多数意見で、夫婦同氏制を合憲と判断し抗告を棄却した。制度の在り方は国会で論じられるべきとした。",
    dissent: "宇賀判事は、夫婦同姓を婚姻の要件とすることは当事者の自由かつ平等な意思決定を妨げるものであり、憲法24条の趣旨に反して違憲であると判断。同種の他の裁判でも一貫して同様の立場を示している。",
    significance: "宇賀・宮崎の2名が違憲の反対意見、三浦守が違憲寄りの「意見」を付し、計3名が現行制度に否定的な見解を示した。行政法学者として行政事件以外でも積極的に個別意見を述べる姿勢が表れている。",
    quote: "",
  },
  {
    id: "uga-sei",
    judgeId: "uga",
    judgeName: "宇賀 克也",
    judgeBackground: "学者",
    date: "2023年10月25日",
    court: "最高裁判所 大法廷",
    caseName: "性同一性障害特例法・生殖不能要件違憲決定",
    caseNumber: "",
    opinionType: "反対意見",
    topic: "性的少数者の権利",
    field: "憲法・人権",
    topicColor: "#0891b2",
    hanreiUrl: "https://www.courts.go.jp/hanrei/92527/detail2/index.html",
    outcome: "生殖不能要件は違憲・無効",
    outcomeKind: "違憲",
    aiSummary: "性別変更に生殖不能手術を求める規定を大法廷が全員一致で違憲とした決定で、宇賀判事はさらに踏み込み、申立人の性別変更を認めるべきだとする反対意見を述べた。外観要件についても違憲の立場を示した。",
    background: "戸籍上の性別変更に「生殖腺がないこと等」を求める性同一性障害特例法3条1項4号の合憲性が争われた。",
    majority: "大法廷は全員一致で生殖不能要件を憲法13条違反と判断。ただし外観要件については高裁に審理を差し戻した。",
    dissent: "宇賀判事は、生殖不能要件は身体の自由を含む個人の尊重を定めた憲法13条に違反すると指摘。さらに外観要件についても、手術を受けるか性別変更を諦めるかの過酷な二者択一を迫るもので違憲とし、申立人の性別変更を認めるべきだと述べた。",
    significance: "多数意見が外観要件の判断を留保する中、宇賀判事は外観要件まで踏み込んで違憲と論じた。当事者の救済に最も踏み込んだ意見として注目された。",
    quote: "",
  },
  {
    id: "uga-osaki",
    judgeId: "uga",
    judgeName: "宇賀 克也",
    judgeBackground: "学者",
    date: "2025年2月",
    court: "最高裁判所 第一小法廷",
    caseName: "大崎事件 第4次再審請求（特別抗告棄却）",
    caseNumber: "",
    opinionType: "反対意見",
    topic: "再審・刑事手続",
    field: "刑事",
    topicColor: "#dc2626",
    hanreiUrl: "https://www.courts.go.jp/saikosai/about/saibankan/index.html",
    outcome: "再審請求を退け（特別抗告棄却）",
    outcomeKind: "棄却",
    aiSummary: "一貫して無実を訴える原口アヤ子さんの第4次再審請求を最高裁が退けた決定で、宇賀判事は単独で再審を開始すべきとする反対意見を付した。確定判決の有罪の根拠となった証拠の証明力を厳しく問い直した。",
    background: "1979年の大崎事件。親族殺害で有罪が確定した原口アヤ子さんが一貫して無実を主張し、再審請求を重ねてきた。本件は4度目の請求。",
    majority: "多数意見は再審を認めない判断を示し、特別抗告を棄却。再審開始のハードルを維持した。",
    dissent: "宇賀判事は、救命救急医の鑑定の信用性を認めた上で、複数回の再審請求事件は過去の審理の証拠も含めて総合評価すべきと指摘。確定判決で有罪の根拠となった証拠は証明力がもはや無きに等しく、殺人事件であることの直接証拠は皆無だとして、再審を開始すべきと述べた。",
    significance: "宇賀判事は名張毒ぶどう酒事件でも再審開始の反対意見を付しており、再審の門戸をめぐり一貫した姿勢を示している。刑事手続でも積極的に個別意見を述べる代表例。",
    quote: "",
  },
];

const OPINION_TYPE_STYLE = {
  "反対意見":       { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" },
  "意見（違憲寄り）": { bg: "#fef3c7", text: "#92400e", border: "#fcd34d" },
  "補足意見":       { bg: "#dbeafe", text: "#1e40af", border: "#93c5fd" },
  "多数意見（全員一致）": { bg: "#d1fae5", text: "#065f46", border: "#6ee7b7" },
};

// 訴訟結果のスタイル（ぱっと見で結論が分かるように）
const OUTCOME_STYLE = {
  "違憲": { bg: "#fef2f2", text: "#b91c1c", border: "#fca5a5", icon: "⚠️", label: "違憲判断" },
  "合憲": { bg: "#f1f5f9", text: "#475569", border: "#cbd5e1", icon: "⚖️", label: "合憲判断" },
  "棄却": { bg: "#f8fafc", text: "#64748b", border: "#e2e8f0", icon: "✕", label: "請求退け" },
  "認容": { bg: "#f0fdf4", text: "#15803d", border: "#86efac", icon: "✓", label: "請求認容" },
  "破棄": { bg: "#fffbeb", text: "#b45309", border: "#fcd34d", icon: "↺", label: "原判決破棄" },
};
const getOutcomeStyle = (k) => OUTCOME_STYLE[k] || OUTCOME_STYLE["棄却"];

const JUDGES = [
  { id: "miura",    name: "三浦 守",    background: "検察官", court: "第二小法廷", appointed: "2020年2月",  color: "#166534", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "hayashi",  name: "林 道晴",    background: "裁判官", court: "第三小法廷", appointed: "2020年9月",  color: "#1e3a8a", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "okamura",  name: "岡村 和美",  background: "行政官", court: "第二小法廷", appointed: "2021年2月",  color: "#7f1d1d", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "yasunami", name: "安浪 亮介",  background: "裁判官", court: "第一小法廷", appointed: "2022年2月",  color: "#1e3a8a", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "watanabe", name: "渡邉 惠理子",background: "弁護士", court: "第三小法廷", appointed: "2022年2月",  color: "#4c1d95", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "sakai",    name: "堺 徹",      background: "検察官", court: "第一小法廷", appointed: "2022年9月",  color: "#166534", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "ojima",    name: "尾島 明",    background: "裁判官", court: "第二小法廷", appointed: "2023年1月",  color: "#1e3a8a", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "miyagawa", name: "宮川 美津子",background: "弁護士", court: "第一小法廷", appointed: "2023年2月",  color: "#4c1d95", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "ishikane", name: "石兼 公博",  background: "行政官", court: "第三小法廷", appointed: "2023年9月",  color: "#7f1d1d", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "hiraki",   name: "平木 正洋",  background: "裁判官", court: "第三小法廷", appointed: "2024年2月",  color: "#1e3a8a", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "nakamura", name: "中村 愼",    background: "弁護士", court: "第一小法廷", appointed: "2024年2月",  color: "#4c1d95", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "takasu",   name: "高須 順一",  background: "弁護士", court: "第二小法廷", appointed: "2025年3月",  color: "#4c1d95", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "okino",    name: "沖野 眞已",  background: "学者",   court: "第三小法廷", appointed: "2025年7月",  color: "#78350f", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "ata",      name: "阿多 博文",  background: "裁判官", court: "第一小法廷", appointed: "2025年10月", color: "#1e3a8a", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  { id: "imasaki",  name: "今崎 幸彦",  background: "裁判官", court: "長官",       appointed: "2024年8月",  color: "#0c1a2e", status: "active", termEnd: null, endReason: null, birthYear: null, education: [], career: [] },
  // 退任者（記録として保持。動作確認用サンプル）
  { id: "miyazaki", name: "宮崎 裕子",  background: "弁護士", court: "—",          appointed: "2018年1月",  color: "#4c1d95", status: "retired", termEnd: "2022年6月", endReason: "定年退官", birthYear: null, education: [], career: [] },
  { id: "uga",      name: "宇賀 克也",  background: "学者",   court: "—",          appointed: "2019年3月",  color: "#78350f", status: "retired", termEnd: "2024年3月", endReason: "定年退官", birthYear: null, education: [], career: [] },
];

const BG_STYLE = {
  裁判官: { bg: "#eff6ff", text: "#1d4ed8", dot: "#3b82f6" },
  弁護士: { bg: "#f5f3ff", text: "#6d28d9", dot: "#7c3aed" },
  検察官: { bg: "#f0fdf4", text: "#15803d", dot: "#16a34a" },
  行政官: { bg: "#fef2f2", text: "#b91c1c", dot: "#dc2626" },
  学者:   { bg: "#fffbeb", text: "#b45309", dot: "#d97706" },
};

// マトリクスの分野列（key=集計キー / short=見出し）
const FIELDS = [
  { key: "刑事",          short: "刑事" },
  { key: "民事",          short: "民事" },
  { key: "行政",          short: "行政" },
  { key: "憲法・人権",     short: "人権" },
  { key: "家族法",        short: "家族" },
  { key: "労働",          short: "労働" },
  { key: "税務",          short: "税務" },
  { key: "選挙・民主主義", short: "選挙" },
];

// 個別意見＝多数意見（全員一致）以外。これが単一の集計ソース。
const isIndividualOpinion = (o) => o.opinionType !== "多数意見（全員一致）";
const individualOpinionsOf = (judgeId) =>
  NOTABLE_OPINIONS.filter((o) => o.judgeId === judgeId && isIndividualOpinion(o));

// マトリクスのセル濃淡（赤＝反対。件数が増えるほど濃く）
function matrixCellStyle(v) {
  if (v === 0) return { bg: "#fafafa", color: "#cbd5e1" };
  if (v === 1) return { bg: "#fee2e2", color: "#991b1b" };
  if (v === 2) return { bg: "#fca5a5", color: "#7f1d1d" };
  if (v === 3) return { bg: "#f87171", color: "#ffffff" };
  if (v === 4) return { bg: "#ef4444", color: "#ffffff" };
  return { bg: "#dc2626", color: "#ffffff" };
}

// =====================
// コンポーネント
// =====================

function OpinionCard({ opinion, onClick, isSelected }) {
  const ts = OPINION_TYPE_STYLE[opinion.opinionType] || OPINION_TYPE_STYLE["反対意見"];
  return (
    <div
      onClick={() => onClick(opinion)}
      style={{
        background: "white",
        borderRadius: 16,
        padding: "20px 22px",
        cursor: "pointer",
        border: isSelected ? "2px solid #0f172a" : "2px solid #f1f5f9",
        boxShadow: isSelected ? "0 8px 30px rgba(0,0,0,0.12)" : "0 2px 8px rgba(0,0,0,0.05)",
        transition: "all 0.2s",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* 左アクセントライン */}
      <div style={{
        position: "absolute", left: 0, top: 0, bottom: 0, width: 4,
        background: opinion.topicColor,
      }} />
      <div style={{ paddingLeft: 8 }}>
        {/* ヘッダー */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          <span style={{
            fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20,
            background: ts.bg, color: ts.text, border: `1px solid ${ts.border}`,
          }}>{opinion.opinionType}</span>
          <span style={{
            fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 20,
            background: `${opinion.topicColor}15`, color: opinion.topicColor,
          }}>{opinion.topic}</span>
        </div>
        {/* 訴訟結果 */}
        {opinion.outcome && (() => {
          const os = getOutcomeStyle(opinion.outcomeKind);
          return (
            <div style={{
              display: "flex", alignItems: "center", gap: 8, marginBottom: 12,
              padding: "8px 12px", borderRadius: 8,
              background: os.bg, border: `1px solid ${os.border}`,
            }}>
              <span style={{ fontSize: 13 }}>{os.icon}</span>
              <span style={{ fontSize: 10, fontWeight: 700, color: os.text, letterSpacing: 0.5 }}>結果</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: os.text }}>{opinion.outcome}</span>
            </div>
          );
        })()}
        <div style={{ fontSize: 15, fontWeight: 700, color: "#0f172a", marginBottom: 6, lineHeight: 1.4 }}>
          {opinion.caseName}
        </div>
        <div style={{ fontSize: 12, color: "#64748b", marginBottom: 10 }}>
          {opinion.date}　{opinion.court}
          {opinion.caseNumber && (
            <span style={{ display: "inline-block", marginLeft: 8, padding: "1px 7px", borderRadius: 6, background: "#f1f5f9", color: "#475569", fontSize: 11 }}>
              {opinion.caseNumber}
            </span>
          )}
        </div>
        <div style={{
          fontSize: 13, color: "#334155", lineHeight: 1.7,
          display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
        }}>
          {opinion.aiSummary}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
          <div style={{
            width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
            background: `linear-gradient(135deg, ${JUDGES.find(j=>j.id===opinion.judgeId)?.color || "#333"}, #00000066)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", fontSize: 11, fontWeight: 700,
          }}>{opinion.judgeName[0]}</div>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#475569" }}>{opinion.judgeName}</span>
          <span style={{
            fontSize: 11, padding: "2px 8px", borderRadius: 10,
            background: BG_STYLE[opinion.judgeBackground]?.bg,
            color: BG_STYLE[opinion.judgeBackground]?.text,
          }}>{opinion.judgeBackground}出身</span>
        </div>
      </div>
    </div>
  );
}

function OpinionDetail({ opinion, onClose }) {
  const ts = OPINION_TYPE_STYLE[opinion.opinionType] || OPINION_TYPE_STYLE["反対意見"];
  const judge = JUDGES.find(j => j.id === opinion.judgeId);
  return (
    <div style={{
      background: "white", borderRadius: 20,
      border: "2px solid #0f172a",
      overflow: "hidden",
    }}>
      {/* ヘッダー */}
      <div style={{
        background: `linear-gradient(135deg, #0f172a 0%, #1e293b 100%)`,
        padding: "28px 28px 24px",
        position: "relative",
      }}>
        <button onClick={onClose} style={{
          position: "absolute", top: 16, right: 16,
          background: "rgba(255,255,255,0.1)", border: "none",
          color: "white", borderRadius: "50%", width: 32, height: 32,
          cursor: "pointer", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center",
        }}>✕</button>
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <span style={{
            fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20,
            background: ts.bg, color: ts.text,
          }}>{opinion.opinionType}</span>
          <span style={{
            fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 20,
            background: `${opinion.topicColor}30`, color: opinion.topicColor,
          }}>{opinion.topic}</span>
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: "white", lineHeight: 1.4, marginBottom: 8 }}>
          {opinion.caseName}
        </div>
        <div style={{ fontSize: 12, color: "#94a3b8" }}>
          {opinion.date}　{opinion.court}
          {opinion.caseNumber && <>　事件番号: {opinion.caseNumber}</>}
        </div>
      </div>

      <div style={{ padding: "24px 28px" }}>
        {/* 訴訟結果バナー */}
        {opinion.outcome && (() => {
          const os = getOutcomeStyle(opinion.outcomeKind);
          return (
            <div style={{
              display: "flex", alignItems: "center", gap: 14, marginBottom: 20,
              padding: "16px 18px", borderRadius: 12,
              background: os.bg, border: `1.5px solid ${os.border}`,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                background: "white", fontSize: 20,
              }}>{os.icon}</div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: os.text, letterSpacing: 1, marginBottom: 2, opacity: 0.8 }}>
                  判決の結果 ・ {os.label}
                </div>
                <div style={{ fontSize: 16, fontWeight: 700, color: os.text }}>{opinion.outcome}</div>
              </div>
            </div>
          );
        })()}
        {/* 担当判事 */}
        <div style={{
          display: "flex", alignItems: "center", gap: 12, marginBottom: 24,
          padding: "14px 16px", background: "#f8fafc", borderRadius: 12,
        }}>
          <div style={{
            width: 44, height: 44, borderRadius: "50%",
            background: `linear-gradient(135deg, ${judge?.color || "#333"}, #00000066)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", fontSize: 16, fontWeight: 700, flexShrink: 0,
          }}>{opinion.judgeName[0]}</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#0f172a" }}>{opinion.judgeName}</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>{opinion.judgeBackground}出身 / {judge?.court} / {judge?.appointed}就任</div>
          </div>
        </div>

        {/* AI要約 */}
        <Section title="🤖 ひとことで言うと" color="#eff6ff" textColor="#1d4ed8">
          {opinion.aiSummary}
        </Section>

        {/* 背景 */}
        <Section title="📋 事件の背景" color="#f8fafc" textColor="#334155">
          {opinion.background}
        </Section>

        {/* 多数意見 */}
        <Section title="⚖️ 多数意見（裁判所の判断）" color="#f0fdf4" textColor="#166534">
          {opinion.majority}
        </Section>

        {/* 個別意見 */}
        <Section
          title={`✍️ ${opinion.judgeName}判事の${opinion.opinionType}`}
          color={ts.bg} textColor={ts.text}
          highlight
        >
          {opinion.dissent}
        </Section>

        {/* 引用 */}
        {opinion.quote && (
          <div style={{
            margin: "16px 0",
            padding: "16px 20px",
            background: "#fafafa",
            borderLeft: `4px solid ${opinion.topicColor}`,
            borderRadius: "0 8px 8px 0",
          }}>
            <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 6, letterSpacing: 1 }}>判決文より抜粋</div>
            <div style={{ fontSize: 13, color: "#334155", lineHeight: 1.8, fontStyle: "italic" }}>
              「{opinion.quote}」
            </div>
          </div>
        )}

        {/* 意義 */}
        <Section title="💡 この判決の意義" color="#fffbeb" textColor="#92400e">
          {opinion.significance}
        </Section>

        {/* リンク */}
        <a
          href={opinion.hanreiUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "flex", alignItems: "center", gap: 8, justifyContent: "center",
            marginTop: 20, padding: "12px",
            background: "#0f172a", color: "white", borderRadius: 10,
            textDecoration: "none", fontSize: 13, fontWeight: 600,
          }}
        >
          📄 最高裁判所 判例全文を読む →
        </a>
      </div>
    </div>
  );
}

function Section({ title, color, textColor, children, highlight }) {
  return (
    <div style={{
      marginBottom: 14,
      background: color,
      borderRadius: 10,
      padding: "14px 16px",
      border: highlight ? `1px solid ${textColor}40` : "none",
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: textColor, marginBottom: 8, letterSpacing: 0.5 }}>
        {title}
      </div>
      <div style={{ fontSize: 13, color: "#334155", lineHeight: 1.8 }}>{children}</div>
    </div>
  );
}

// 分野マトリクス：判事 × 分野で個別意見の集中を可視化
function DissentMatrix({ onJudgeClick }) {
  const [hover, setHover] = useState({ row: null, col: null });

  const rows = JUDGES
    .map((j) => {
      const ops = individualOpinionsOf(j.id);
      const byField = {};
      FIELDS.forEach((f) => {
        byField[f.key] = ops.filter((o) => o.field === f.key).length;
      });
      return { judge: j, byField, total: ops.length };
    })
    .filter((r) => r.total > 0)
    .sort((a, b) => b.total - a.total);

  const fieldTotals = {};
  FIELDS.forEach((f) => {
    fieldTotals[f.key] = rows.reduce((s, r) => s + r.byField[f.key], 0);
  });
  const grand = rows.reduce((s, r) => s + r.total, 0);

  const headBase = {
    display: "flex", alignItems: "flex-end", justifyContent: "center",
    padding: "4px 0", fontSize: 12, transition: "color 0.1s",
  };

  return (
    <div>
      {/* 説明バナー */}
      <div style={{
        background: "white", borderRadius: 12, padding: "14px 18px",
        marginBottom: 18, display: "flex", gap: 12, alignItems: "flex-start",
        border: "1px solid #e2e8f0",
      }}>
        <span style={{ fontSize: 20 }}>📊</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>分野マトリクスとは？</div>
          <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.7 }}>
            どの判事がどの法律分野で個別意見（反対意見・意見・補足意見）を述べているかを集計したものです。色が濃い（赤い）ほど件数が多く、判事ごとの関心や judicial philosophy が読み取れます。判事名をタップすると詳細を表示します。
          </div>
        </div>
      </div>

      {rows.length === 0 ? (
        <div style={{
          background: "white", borderRadius: 12, padding: "40px 24px",
          textAlign: "center", color: "#94a3b8", fontSize: 13, border: "1px solid #e2e8f0",
        }}>
          個別意見データを収集中です。データが追加されると自動的にマトリクスが生成されます。
        </div>
      ) : (
        <div style={{
          background: "white", borderRadius: 12, padding: "18px 16px",
          border: "1px solid #e2e8f0", overflowX: "auto",
        }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: `92px repeat(${FIELDS.length}, minmax(40px, 1fr)) 40px`,
            gap: 3, alignItems: "stretch", minWidth: 520,
          }}>
            {/* ヘッダー行 */}
            <div />
            {FIELDS.map((f, ci) => (
              <div key={f.key} style={{
                ...headBase,
                color: hover.col === ci ? "#0f172a" : "#94a3b8",
                fontWeight: hover.col === ci ? 700 : 400,
              }}>{f.short}</div>
            ))}
            <div style={{ ...headBase, color: "#94a3b8" }}>計</div>

            {/* 判事行 */}
            {rows.map((r) => (
              <RowFragment
                key={r.judge.id}
                r={r}
                hover={hover}
                setHover={setHover}
                onJudgeClick={onJudgeClick}
              />
            ))}

            {/* 分野計 */}
            <div style={{ display: "flex", alignItems: "center", fontSize: 11, color: "#94a3b8", paddingTop: 6 }}>分野計</div>
            {FIELDS.map((f) => (
              <div key={f.key} style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 12, fontWeight: 700, color: "#64748b", paddingTop: 6,
              }}>{fieldTotals[f.key]}</div>
            ))}
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 12, fontWeight: 700, color: "#94a3b8", paddingTop: 6,
            }}>{grand}</div>
          </div>
        </div>
      )}

      {/* 凡例 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 14, fontSize: 11, color: "#94a3b8" }}>
        <span>少</span>
        {["#fee2e2", "#fca5a5", "#f87171", "#dc2626"].map((c) => (
          <span key={c} style={{ width: 18, height: 12, background: c, borderRadius: 3 }} />
        ))}
        <span>多</span>
      </div>

      <div style={{
        marginTop: 14, padding: "12px 16px", borderRadius: 10,
        background: "#fffbeb", border: "1px solid #fcd34d",
        fontSize: 11, color: "#92400e", lineHeight: 1.7,
      }}>
        ⚠️ 空欄はその分野で個別意見がないことを示し、賛成を意味しません（そもそも該当事件が来ていない場合を含む）。複数分野にまたがる事件は主たる争点で1分類に集計しています。現在はサンプルデータのため、スクレイパーによる全判事データ収集後に本領を発揮します。
      </div>
    </div>
  );
}

function RowFragment({ r, hover, setHover, onJudgeClick }) {
  const { judge, byField, total } = r;
  return (
    <>
      <div
        onClick={() => onJudgeClick(judge.id)}
        style={{
          display: "flex", flexDirection: "column", justifyContent: "center",
          cursor: "pointer", paddingRight: 6,
        }}
      >
        <span style={{
          fontSize: 13, fontWeight: 700,
          color: hover.row === judge.id ? "#0891b2" : "#0f172a",
        }}>{judge.name}</span>
        <span style={{ fontSize: 10, color: "#94a3b8" }}>{judge.appointed}就任</span>
      </div>
      {FIELDS.map((f, ci) => {
        const v = byField[f.key];
        const s = matrixCellStyle(v);
        return (
          <div
            key={f.key}
            onMouseEnter={() => setHover({ row: judge.id, col: ci })}
            onMouseLeave={() => setHover({ row: null, col: null })}
            style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              height: 34, borderRadius: 4, fontSize: 13,
              background: s.bg, color: s.color,
            }}
          >{v === 0 ? "·" : v}</div>
        );
      })}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: 34, fontSize: 13, fontWeight: 700, color: "#0f172a",
      }}>{total}</div>
    </>
  );
}

// =====================
// メイン
// =====================
export default function App() {
  const [tab, setTab] = useState("opinions"); // opinions | judges | matrix
  const [selectedOpinion, setSelectedOpinion] = useState(null);
  const opinionListScrollY = useRef(0); // 詳細を開く前の一覧位置を記憶
  const [filterType, setFilterType] = useState("全て");
  const [scrollTarget, setScrollTarget] = useState(null); // マトリクスから来た時の一度きりのスクロール対象
  const [openJudges, setOpenJudges] = useState(() => new Set()); // 開いているカード（複数可）
  const [query, setQuery] = useState(""); // 全体横断検索（裁判官名・事件名・事件番号）

  // 画面幅を監視（タブのコンパクト表示切り替え用）
  const [vw, setVw] = useState(typeof window !== "undefined" ? window.innerWidth : 1024);
  useEffect(() => {
    const onResize = () => setVw(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const compactTabs = vw < 480;
  const toggleJudge = (id) => {
    setOpenJudges(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };
  const [judgeStatus, setJudgeStatus] = useState("現職"); // 現職 | 退任 | 全て
  const [sortKey, setSortKey] = useState("appointed_desc");

  const q = query.trim().toLowerCase();
  const opinionMatchesQuery = (o) => {
    if (!q) return true;
    return [o.judgeName, o.caseName, o.caseNumber, o.topic]
      .filter(Boolean)
      .some(v => v.toLowerCase().includes(q));
  };

  const opinionTypes = ["全て", "反対意見", "意見（違憲寄り）", "補足意見", "多数意見（全員一致）"];
  const filteredOpinions = NOTABLE_OPINIONS
    .filter(o => filterType === "全て" || o.opinionType === filterType)
    .filter(opinionMatchesQuery);

  const activeCount = JUDGES.filter(j => j.status === "active").length;
  const retiredCount = JUDGES.filter(j => j.status === "retired").length;

  // "2020年2月" → 202002 の数値に（ソート用）
  const ymNum = (s) => {
    if (!s) return 0;
    const m = s.match(/(\d+)年(\d+)月/);
    return m ? parseInt(m[1]) * 100 + parseInt(m[2]) : 0;
  };
  const indivCount = (id) => individualOpinionsOf(id).length;

  const SORT_OPTIONS = [
    { key: "appointed_desc", label: "就任日（新しい順）" },
    { key: "appointed_asc",  label: "就任日（古い順）" },
    { key: "opinions_desc",  label: "個別意見数（多い順）" },
    { key: "background",     label: "出身別" },
    { key: "name",           label: "氏名順" },
  ];

  const sortJudges = (arr) => {
    const a = [...arr];
    switch (sortKey) {
      case "appointed_asc":  return a.sort((x, y) => ymNum(x.appointed) - ymNum(y.appointed));
      case "opinions_desc":  return a.sort((x, y) => indivCount(y.id) - indivCount(x.id) || ymNum(y.appointed) - ymNum(x.appointed));
      case "background":     return a.sort((x, y) => x.background.localeCompare(y.background, "ja") || ymNum(y.appointed) - ymNum(x.appointed));
      case "name":           return a.sort((x, y) => x.name.localeCompare(y.name, "ja"));
      case "appointed_desc":
      default:               return a.sort((x, y) => ymNum(y.appointed) - ymNum(x.appointed));
    }
  };

  const judgeMatchesQuery = (j) => {
    if (!q) return true;
    if (j.name.toLowerCase().includes(q) || j.background.toLowerCase().includes(q)) return true;
    // 担当した事件名・事件番号でもヒットさせる
    return NOTABLE_OPINIONS.some(o => o.judgeId === j.id &&
      [o.caseName, o.caseNumber].filter(Boolean).some(v => v.toLowerCase().includes(q)));
  };

  const visibleJudges = sortJudges(
    JUDGES
      .filter(j => judgeStatus === "全て" ? true : judgeStatus === "現職" ? j.status === "active" : j.status === "retired")
      .filter(judgeMatchesQuery)
  );

  const goToJudge = (id) => {
    setTab("judges");
    setJudgeStatus("全て");
    setOpenJudges(prev => new Set(prev).add(id));
    setScrollTarget(id);
  };

  // タブを手動切替したとき、ヘッダーが隠れていれば「タブのみ表示」位置を保つ
  const changeTab = (key) => {
    const headerH = titleHeaderRef.current ? titleHeaderRef.current.getBoundingClientRect().height : 0;
    const wasPastHeader = window.pageYOffset >= headerH - 1;
    setTab(key);
    requestAnimationFrame(() => {
      if (wasPastHeader) {
        // ヘッダーは隠れたまま・タブだけ見える位置にスナップ（中身は先頭から）
        window.scrollTo({ top: headerH, behavior: "auto" });
      } else {
        window.scrollTo({ top: 0, behavior: "auto" });
      }
    });
  };

  // マトリクスから飛んだ時だけ、一度スクロールして即クリア（通常操作には干渉しない）
  const judgeRefs = useRef({});
  const tabBarRef = useRef(null);
  const titleHeaderRef = useRef(null);

  // 「上に戻る」ボタンの表示制御
  const [showTop, setShowTop] = useState(false);
  useEffect(() => {
    const onScroll = () => setShowTop(window.pageYOffset > 600);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffect(() => {
    if (!scrollTarget) return;
    let raf1, raf2;
    // タブ切替＋カード展開の描画が確定してから測定・スクロールする
    const t = setTimeout(() => {
      raf1 = requestAnimationFrame(() => {
        raf2 = requestAnimationFrame(() => {
          const el = judgeRefs.current[scrollTarget];
          if (el) {
            // 固定タブの実測高さぶんを scroll-margin-top に当て、容器に依存せず正確に下げる
            const barH = tabBarRef.current ? tabBarRef.current.getBoundingClientRect().height : 48;
            el.style.scrollMarginTop = (barH + 28) + "px";
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
          setScrollTarget(null);
        });
      });
    }, 60);
    return () => { clearTimeout(t); cancelAnimationFrame(raf1); cancelAnimationFrame(raf2); };
  }, [scrollTarget]);

  return (
    <div style={{ fontFamily: "'Noto Serif JP', Georgia, serif", background: "#f1f5f9", minHeight: "100vh" }}>

      {/* ヘッダー */}
      <div ref={titleHeaderRef} style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        color: "white", padding: "36px 20px 28px",
      }}>
        <div style={{ maxWidth: 860, margin: "0 auto" }}>
          <div style={{ fontSize: 10, letterSpacing: 5, color: "#64748b", marginBottom: 10, textTransform: "uppercase" }}>
            Supreme Court Watch
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 8px", lineHeight: 1.3 }}>
            最高裁判所<br/>
            <span style={{ fontSize: 14, fontWeight: 400, color: "#94a3b8" }}>裁判官データベース</span>
          </h1>
          <p style={{ fontSize: 12, color: "#64748b", margin: "10px 0 24px", lineHeight: 1.8 }}>
            現職{activeCount}名の裁判官の経歴・反対意見・国民審査情報を公開情報から整理しています
          </p>
        </div>
      </div>

      {/* タブ（上部固定） */}
      <div ref={tabBarRef} style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "#1e293b",
        boxShadow: "0 2px 10px rgba(0,0,0,0.15)",
      }}>
        <div style={{
          maxWidth: 860, margin: "0 auto", padding: "0 12px",
          display: "flex", gap: 2,
          flexWrap: "nowrap", overflowX: "auto",
          WebkitOverflowScrolling: "touch", scrollbarWidth: "none",
        }}>
          {[
            { key: "opinions", long: "📝 注目の個別意見", short: "📝 意見" },
            { key: "judges",   long: "👤 裁判官一覧",     short: "👤 一覧" },
            { key: "matrix",   long: "📊 分野マトリクス", short: "📊 分野" },
          ].map(t => (
            <button key={t.key} onClick={() => changeTab(t.key)} style={{
              flex: compactTabs ? "1 1 0" : "0 0 auto",
              whiteSpace: "nowrap",
              padding: compactTabs ? "12px 8px" : "12px 18px",
              border: "none", cursor: "pointer",
              fontSize: compactTabs ? 12 : 13, fontWeight: 700,
              background: "transparent",
              color: tab === t.key ? "#fff" : "#94a3b8",
              borderBottom: tab === t.key ? "3px solid #f87171" : "3px solid transparent",
              transition: "color 0.2s",
            }}>{compactTabs ? t.short : t.long}</button>
          ))}
        </div>
        {/* 全体横断検索 */}
        <div style={{ background: "#0f172a" }}>
          <div style={{ maxWidth: 860, margin: "0 auto", padding: "8px 12px", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: "#64748b", fontSize: 14 }}>🔍</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="裁判官名・事件名・事件番号で検索"
              style={{
                flex: 1, minWidth: 0,
                background: "#1e293b", color: "#fff",
                border: "1px solid #334155", borderRadius: 8,
                padding: "8px 12px", fontSize: 13, fontFamily: "inherit",
                outline: "none",
              }}
            />
            {query && (
              <button onClick={() => setQuery("")} aria-label="検索クリア" style={{
                background: "transparent", border: "none", color: "#94a3b8",
                cursor: "pointer", fontSize: 16, padding: "4px 6px",
              }}>✕</button>
            )}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 860, margin: "0 auto", padding: "24px 16px" }}>

        {/* 個別意見タブ */}
        {tab === "opinions" && (
          <div>
            {selectedOpinion ? (
              <OpinionDetail opinion={selectedOpinion} onClose={() => { const y = opinionListScrollY.current; setSelectedOpinion(null); requestAnimationFrame(() => window.scrollTo({ top: y, behavior: "auto" })); }} />
            ) : (
              <>
                {/* フィルター */}
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 8, letterSpacing: 1 }}>意見種別で絞り込む</div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {opinionTypes.map(t => {
                      const ts = OPINION_TYPE_STYLE[t];
                      return (
                        <button key={t} onClick={() => setFilterType(t)} style={{
                          padding: "6px 14px", borderRadius: 20, cursor: "pointer",
                          fontSize: 12, fontWeight: 600, transition: "all 0.2s",
                          background: filterType === t ? (ts?.bg || "#0f172a") : "#e2e8f0",
                          color: filterType === t ? (ts?.text || "white") : "#64748b",
                          border: filterType === t && ts ? `1px solid ${ts.border}` : "1px solid transparent",
                        }}>{t}</button>
                      );
                    })}
                  </div>
                </div>

                {/* 説明バナー */}
                <div style={{
                  background: "white", borderRadius: 12, padding: "14px 18px",
                  marginBottom: 20, display: "flex", gap: 12, alignItems: "flex-start",
                  border: "1px solid #e2e8f0",
                }}>
                  <span style={{ fontSize: 20 }}>ℹ️</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>個別意見とは？</div>
                    <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.7 }}>
                      最高裁の裁判官は全員が判決書に意見を表示する義務があります。多数意見に反対する「反対意見」、結論は同じでも理由が異なる「意見」、多数意見を補足する「補足意見」があります。個別意見は裁判官の思想・価値観が最もよく現れる部分です。
                    </div>
                  </div>
                </div>

                {/* カード一覧 */}
                <div style={{ display: "grid", gap: 14 }}>
                  {filteredOpinions.map(opinion => (
                    <OpinionCard
                      key={opinion.id}
                      opinion={opinion}
                      onClick={(op) => { opinionListScrollY.current = window.pageYOffset; setSelectedOpinion(op); requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" })); }}
                      isSelected={selectedOpinion?.id === opinion.id}
                    />
                  ))}
                  {filteredOpinions.length === 0 && (
                    <div style={{ background: "white", borderRadius: 12, padding: "32px 20px", textAlign: "center", color: "#94a3b8", fontSize: 13, border: "1px solid #e2e8f0" }}>
                      「{query}」に一致する意見は見つかりませんでした
                    </div>
                  )}
                </div>

                {/* データ収集中バナー */}
                <div style={{
                  marginTop: 24, padding: "14px 18px", borderRadius: 12,
                  background: "#fffbeb", border: "1px solid #fcd34d",
                  fontSize: 12, color: "#92400e", lineHeight: 1.7,
                }}>
                  ⚠️ 現在は三浦守・林道晴・宇賀克也（退任）各判事の主要意見を掲載しています。スクレイパーによる全判事データ収集後、順次追加予定です。
                </div>
              </>
            )}
          </div>
        )}

        {/* 裁判官一覧タブ */}
        {tab === "judges" && (
          <div>
            {/* フィルター + ソート */}
            <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {[
                  { key: "現職", label: `現職 ${activeCount}名` },
                  { key: "退任", label: `退任 ${retiredCount}名` },
                  { key: "全て", label: "全て" },
                ].map(s => (
                  <button key={s.key} onClick={() => setJudgeStatus(s.key)} style={{
                    padding: "6px 16px", borderRadius: 20, border: "none", cursor: "pointer",
                    fontSize: 12, fontWeight: 700, transition: "all 0.2s",
                    background: judgeStatus === s.key ? "#0f172a" : "#e2e8f0",
                    color: judgeStatus === s.key ? "white" : "#64748b",
                  }}>{s.label}</button>
                ))}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {openJudges.size > 0 && (
                  <button onClick={() => setOpenJudges(new Set())} style={{
                    fontSize: 11, fontWeight: 600, color: "#64748b",
                    padding: "7px 12px", borderRadius: 8,
                    border: "1px solid #cbd5e1", background: "white", cursor: "pointer",
                    fontFamily: "inherit",
                  }}>すべて閉じる</button>
                )}
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 11, color: "#94a3b8" }}>並び替え</span>
                  <select
                    value={sortKey}
                    onChange={(e) => setSortKey(e.target.value)}
                    style={{
                      fontSize: 12, fontWeight: 600, color: "#0f172a",
                      padding: "7px 10px", borderRadius: 8,
                      border: "1px solid #cbd5e1", background: "white", cursor: "pointer",
                      fontFamily: "inherit",
                    }}
                  >
                    {SORT_OPTIONS.map(o => (
                      <option key={o.key} value={o.key}>{o.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gap: 10 }}>
            {visibleJudges.length === 0 && (
              <div style={{ background: "white", borderRadius: 12, padding: "32px 20px", textAlign: "center", color: "#94a3b8", fontSize: 13, border: "1px solid #e2e8f0" }}>
                {query ? `「${query}」に一致する裁判官は見つかりませんでした` : "該当する裁判官がいません"}
              </div>
            )}
            {visibleJudges.map(judge => {
              const bs = BG_STYLE[judge.background] || BG_STYLE["裁判官"];
              const judgeOpinions = NOTABLE_OPINIONS.filter(o => o.judgeId === judge.id);
              const individualCount = judgeOpinions.filter(isIndividualOpinion).length;
              const isOpen = openJudges.has(judge.id);
              return (
                <div key={judge.id}
                  ref={(el) => { judgeRefs.current[judge.id] = el; }}
                  onClick={() => toggleJudge(judge.id)}
                  style={{
                    background: "white", borderRadius: 12, padding: "16px 18px",
                    cursor: "pointer",
                    border: isOpen ? "2px solid #0f172a" : "2px solid transparent",
                    boxShadow: isOpen ? "0 4px 20px rgba(0,0,0,0.1)" : "0 1px 4px rgba(0,0,0,0.05)",
                    transition: "all 0.2s", position: "relative", overflow: "hidden",
                  }}
                >
                  <div style={{
                    position: "absolute", left: 0, top: 0, bottom: 0, width: 4,
                    background: judge.color,
                  }} />
                  <div style={{ display: "flex", alignItems: "center", gap: 14, paddingLeft: 8 }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: "50%", flexShrink: 0,
                      background: `linear-gradient(135deg, ${judge.color}, #00000066)`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "white", fontSize: 16, fontWeight: 700,
                    }}>{judge.name[0]}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 16, fontWeight: 700, color: "#0f172a" }}>{judge.name}</span>
                        {judge.court === "長官" && (
                          <span style={{ fontSize: 10, background: "#0f172a", color: "white", padding: "2px 8px", borderRadius: 10, fontWeight: 700 }}>長官</span>
                        )}
                        {judge.status === "retired" && (
                          <span style={{ fontSize: 10, background: "#e2e8f0", color: "#475569", padding: "2px 8px", borderRadius: 10, fontWeight: 700 }}>退任</span>
                        )}
                        {individualCount > 0 && (
                          <span style={{ fontSize: 10, background: "#fee2e2", color: "#991b1b", padding: "2px 8px", borderRadius: 10, fontWeight: 700 }}>
                            個別意見 {individualCount}件
                          </span>
                        )}
                      </div>
                      <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 10, background: bs.bg, color: bs.text, fontWeight: 600 }}>{judge.background}出身</span>
                        <span style={{ fontSize: 11, color: "#94a3b8" }}>{judge.court}</span>
                        <span style={{ fontSize: 11, color: "#94a3b8" }}>
                          {judge.appointed}就任{judge.termEnd ? ` 〜 ${judge.termEnd}退任` : ""}
                        </span>
                      </div>
                    </div>
                    <div style={{ color: "#cbd5e1", fontSize: 14 }}>{isOpen ? "▲" : "▼"}</div>
                  </div>

                  {isOpen && (
                    <div style={{ marginTop: 16, paddingLeft: 8 }}>
                      <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 10, letterSpacing: 1 }}>📚 経歴</div>
                      {(judge.education.length > 0 || judge.career.length > 0) ? (
                        <div style={{ background: "#f8fafc", borderRadius: 8, padding: "12px 14px", border: "1px solid #e2e8f0", marginBottom: 16 }}>
                          {judge.birthYear && (
                            <div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>生年: {judge.birthYear}年</div>
                          )}
                          {judge.education.length > 0 && (
                            <div style={{ fontSize: 12, color: "#334155", marginBottom: 6 }}>学歴: {judge.education.join(" / ")}</div>
                          )}
                          {judge.career.length > 0 && (
                            <div style={{ fontSize: 12, color: "#334155" }}>主な歴任: {judge.career.join(" → ")}</div>
                          )}
                          {judge.endReason && (
                            <div style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>退任事由: {judge.endReason}</div>
                          )}
                        </div>
                      ) : (
                        <div style={{
                          background: "#f8fafc", borderRadius: 8, padding: "14px",
                          border: "1px dashed #cbd5e1", marginBottom: 16,
                          fontSize: 12, color: "#94a3b8", textAlign: "center",
                        }}>
                          経歴データは courts.go.jp から自動取得予定（scraper連携）
                        </div>
                      )}
                    </div>
                  )}

                  {isOpen && judgeOpinions.length > 0 && (
                    <div style={{ marginTop: 0, paddingLeft: 8 }}>
                      <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 10, letterSpacing: 1 }}>掲載中の注目意見</div>
                      {judgeOpinions.map(op => (
                        <div key={op.id}
                          onClick={(e) => { e.stopPropagation(); opinionListScrollY.current = 0; setSelectedOpinion(op); changeTab("opinions"); }}
                          style={{
                            padding: "10px 14px", borderRadius: 8, marginBottom: 8,
                            background: "#f8fafc", border: "1px solid #e2e8f0",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ display: "flex", gap: 6, marginBottom: 4 }}>
                            <span style={{
                              fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 10,
                              background: OPINION_TYPE_STYLE[op.opinionType]?.bg || "#fee2e2",
                              color: OPINION_TYPE_STYLE[op.opinionType]?.text || "#991b1b",
                            }}>{op.opinionType}</span>
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>{op.caseName}</div>
                          <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>{op.date} — 詳細を読む →</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {isOpen && judgeOpinions.length === 0 && (
                    <div style={{ marginTop: 14, paddingLeft: 8, fontSize: 12, color: "#94a3b8" }}>
                      個別意見データは収集中です
                    </div>
                  )}
                </div>
              );
            })}
            </div>
          </div>
        )}

        {/* 分野マトリクスタブ */}
        {tab === "matrix" && (
          <DissentMatrix onJudgeClick={goToJudge} />
        )}

        <div style={{ marginTop: 40, padding: "16px 0", borderTop: "1px solid #e2e8f0", fontSize: 11, color: "#94a3b8", lineHeight: 1.8 }}>
          <p>データ出典: 最高裁判所公式サイト (courts.go.jp) / 判決文は国の著作物として自由利用可</p>
          <p>AI要約はClaudeによる要約です。正確な内容は判決全文でご確認ください。</p>
          <p>※ 掲載情報は {new Date().getFullYear()}年時点のものです</p>
        </div>
      </div>

      {/* 上に戻るボタン */}
      {showTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          aria-label="上に戻る"
          style={{
            position: "fixed", right: 20, bottom: 24, zIndex: 60,
            width: 48, height: 48, borderRadius: "50%",
            border: "none", cursor: "pointer",
            background: "#0f172a", color: "white",
            boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
            fontSize: 20, display: "flex", alignItems: "center", justifyContent: "center",
            transition: "opacity 0.2s",
          }}
        >↑</button>
      )}
    </div>
  );
}
