# Labelling guide: test-1

Each line of a part file is a Japanese sentence with numbered forms. Each form lists the
grammar uses it may have; the uses are explained below.

Judge each sentence as a careful native reader would. For every form, give each listed use a
probability, the probabilities summing to 1. Be decisive where the sentence is clear: give the
use it has 1. Spread probability only where the sentence itself is ambiguous. Where no listed
use fits, because the form is part of a fixed word or expression or was found by mistake, set
`none_fit` to true and every probability to 0.

Write one JSON object per input line, in the same order, and nothing else:

    {"id": "...", "forms": [{"n": 0, "probabilities": {"wa.topic": 1, "wa.contrast": 0},
      "none_fit": false}]}

on a single line.

Every form of every sentence must appear, with every use it lists.

## Uses

- `causative.let`, let do: Let someone do: 子供を遊ばせる, let the child play; 休ませてください, please let me rest.
- `causative.make`, make do: Make someone do: 子供に野菜を食べさせる, make the child eat vegetables.
- `da`, copula: Joins a noun or na-adjective to what it describes: 猫だ, (it) is a cat.
- `darou.confirm`, right?: With rising intonation, asks the listener to confirm: 行くでしょう?, you're going, right?
- `darou.guess`, probably: The speaker supposes it is so: 明日は雨だろう, it will probably rain tomorrow. でしょう is polite.
- `de.cause`, cause: Marks a cause: 病気で休んだ, was absent because of illness.
- `de.means`, means: Marks the tool, means or material: バスで行く, go by bus; 日本語で話す, speak in Japanese.
- `de.place`, place of action: Marks where an action happens: 図書館で勉強する, study at the library.
- `de.scope`, scope: Marks the group or range something holds within: 世界で一番, the most in the world; 三人で, as a group of three.
- `ga.object`, object of a state: Marks what is liked, wanted, understood or possible, with predicates such as 好き, ほしい, 分かる and できる: 猫が好き, likes cats.
- `ga.subject`, subject: Marks the subject: 雨が降っている, it is raining; 猫がいる, there is a cat. In questions and answers it picks out who or what: 誰が来た?, who came?
- `janai`, isn't it: Not a negative: asks or insists that it is so: いいじゃない, isn't that nice; 雨じゃないか, isn't that rain? のではないか, isn't it the case that, perhaps.
- `ka.embedded`, question inside a sentence: Ends a question that is part of a larger sentence: 何を買うか決めた, (I) decided what to buy.
- `ka.or`, or: Between nouns, offers alternatives: 月曜か火曜, Monday or Tuesday.
- `mo.also`, also: Adds the marked part to something already said, in place of は, が or を: 私も学生だ, I am a student too.
- `mo.even`, emphasis: After an amount, stresses it as large; with one and a negative, not even one: 三時間も待った, waited a whole three hours; 一人も来なかった, not a single person came.
- `nai`, negative: Negates the predicate it ends: 学生じゃない, isn't a student; 高くない, isn't expensive; 行かない, doesn't go. Polite: 行きません, 学生じゃありません.
- `ni.agent`, agent: With a passive or causative verb, marks who does the action: 先生に叱られた, was scolded by the teacher.
- `ni.goal`, destination: Marks where movement ends: 学校に行く, go to school.
- `ni.place`, place of being: Marks where something is, with ある, いる and 住む: 東京に住む, live in Tokyo.
- `ni.purpose`, purpose of going: After a verb stem, before a verb of going or coming, in order to: 買いに行く, go to buy; 遊びに来る, come to visit.
- `ni.rate`, per: After a span of time, the rate: 一日に三回, three times a day.
- `ni.result`, becoming, choosing: Marks what something becomes or is made, with なる and する: 医者になる, become a doctor; コーヒーにする, decide on coffee.
- `ni.target`, recipient or target: Marks the person an action is directed at: 友達に会う, meet a friend; 先生に聞く, ask the teacher.
- `ni.time`, point in time: Marks the time something happens: 三時に起きる, get up at three.
- `no.link`, noun modifier: Makes the noun before it describe the noun after it, by owner, kind, place or whole: 私の本, my book; 日本の車, a Japanese car.
- `no.nominalizer`, nominaliser の: Turns the clause before it into a noun: 泳ぐのが好き, likes swimming.
- `no.one`, the one: Stands for a noun already understood: 赤いの, the red one.
- `noni.despite`, even though: After a clause, even though, with surprise or complaint: 約束したのに来なかった, (he) promised, yet didn't come.
- `noni.purpose`, for: After a dictionary-form verb, for, with words of use or need: 料理するのに使う, use (it) for cooking.
- `o.motion`, place moved through or left: With verbs of motion, marks the place gone through, along or out of: 公園を歩く, walk in the park; 家を出る, leave home.
- `o.object`, object: Marks what the action is done to: 本を読む, read a book.
- `passive.direct`, is done: The subject undergoes the action: 先生に褒められた, was praised by the teacher.
- `passive.respect`, respect: A passive form for the action of someone the speaker respects: 先生が来られた, the teacher came.
- `passive.suffering`, is affected by: The subject is affected, usually badly, by an event: 雨に降られた, got caught in the rain.
- `potential`, can: Can do: 読める, can read; 食べられる, can eat. What can be done often takes が.
- `relative.no-as-subject`, の as subject: Inside such a clause, の can mark the subject in place of が: 友達の買った本, the book my friend bought.
- `tame.cause`, because of: After a clause or Nの that is not a deliberate aim, because of: 事故のために遅れた, was late because of an accident; 時間がないため, as there is no time. Purpose needs a deliberate act in the dictionary form.
- `tame.purpose`, in order to: After a dictionary-form verb or Nの, for the purpose of: 家を買うために働く, work to buy a house.
- `tara.discovery`, when (and found): With a past main clause, when (I) did the first, the second happened or was found: 窓を開けたら雪だった, (I) opened the window and it was snowing.
- `tara.if`, if, once: After a た form, if or once the first happens, the second follows: 着いたら電話する, (I'll) call when (I) arrive.
- `te-iku.away`, go doing: Do and go, or move away while doing: 持っていく, take (it) along.
- `te-iku.change`, change from now on: A change continuing from now on: 増えていく, will keep increasing.
- `te-kuru.change`, change up to now: A change up to now, or starting: 寒くなってきた, it has got cold.
- `te-kuru.toward`, come doing: Do and come back, or toward the speaker: 買ってくる, go and buy (it); 電話をかけてくる, call (me).
- `te-shimau.complete`, finish: Do completely: 全部読んでしまった, (I) read it all.
- `te-shimau.regret`, regret: It happened, to the speaker's regret or by accident: 財布を忘れてしまった, (I) forgot my wallet. Spoken: ちゃう, じゃう.
- `te.and`, and: Joins clauses or predicates in order, or tells how: 起きて食べた, got up and ate; 歩いて行く, go on foot.
- `te.cause`, cause: The first clause gives the cause, often of a feeling: 会えてうれしい, glad to have met (you).
- `teiru.habit`, habit, job: An action repeated over a period, or a job: 毎朝走っている, (I) run every morning these days; 銀行で働いている, works at a bank.
- `teiru.ongoing`, action in progress: The action is under way at the time spoken of: 食べている, is eating.
- `teiru.state`, resulting state: A change has happened and its result holds: 結婚している, is married; 死んでいる, is dead.
- `to-conditional.discovery`, when (and found): With a past main clause, when the first happened, the second was found: ドアを開けると猫がいた, (I) opened the door and there was a cat.
- `to-conditional.whenever`, whenever, if: After a non-past clause, whenever or if the first happens, the second follows naturally: 春になると暖かくなる, when spring comes it gets warm.
- `to.and`, and (complete list): Joins nouns into a complete list: 犬と猫, a dog and a cat.
- `to.quote`, quotation: Ends what is said or thought: 行くと言った, said (he) would go; 高いと思う, (I) think it's expensive.
- `to.with`, with: Marks the partner in an action or comparison: 友達と行く, go with a friend; 兄と同じ, the same as my brother.
- `toiu.called`, called: Xという N, an N called X: 田中という人, a person called Tanaka.
- `toiu.content`, that: A clause with という before a noun gives its content: 彼が来るという噂, the rumour that he is coming.
- `tte.quote`, says, called (spoken): Spoken と or という: 行くって言った, (he) said (he'd) go; 田中って人, a person called Tanaka.
- `tte.topic`, speaking of (spoken): Spoken は when bringing up or defining a topic: 日本語って難しい, Japanese is hard.
- `wa.contrast`, contrast: Sets the marked part against others, often unsaid: 肉は食べない, meat (at least) I don't eat.
- `wa.topic`, topic: Marks what the sentence is about; the rest says something about it: 私は学生だ, I am a student.
- `you.like`, like, as: With の, like, resembling: 夢のような話, a story like a dream; after a clause, as: 前に言ったように, as (I) said before.
- `you.seems`, seems: After a clause, it seems, from what the speaker sees or knows: 雨が降ったようだ, it seems it rained.
- `youni.purpose`, so that: After a non-past verb, usually potential or negative, so that: 聞こえるように話す, speak so (they) can hear.
- `youni.request`, tell to: Before a verb of saying, tells someone to: 来るように言った, told (him) to come.
