# persian-writing — excerpt used by the X pipeline

Verbatim excerpts from github.com/ali2000hos/persian-writing @35eb7a5, `universal/persian-writing-universal.md`
(MIT, see LICENSE in this folder). Sections: register detection + formal-but-human (lines 271-308, 326-359),
Persian AI tells T1-T18 + what not to flag (405-519), orthography §1-8 (652-800), proper names (960-984),
social-channel shared rules incl. emoji/bidi (1268-1307). Cross-references to other files of the skill are not
included. Local rule (measured 2026-09-26): version strings in product names stay Latin (Opus 5.5, GPT-6).


<!-- lines 271,308 -->
## Part 1: Register detection

A register error is the most expensive mistake this skill can make: a خودمونی
proposal loses the client; a stiff Instagram caption loses the audience; a
casual نامه اداری can embarrass the sender in front of an organization. Decide
the register BEFORE writing, using the procedure below — never by feel.

| Context | Register | Markers |
|---|---|---|
| Proposal, invoice, contract, report, official/B2B email, website copy | **Formal-but-human** | Full written forms، شما، no slang — but direct and alive |
| نامه اداری / letter to an organization or authority | **Formal-اداری** | Formal + letter conventions (honorifics, opener/closer — see below) |
| Blog post, newsletter, product update, LinkedIn | **Semi-formal** | Written forms + warm voice، direct address، occasional colloquial word |
| Instagram, Telegram, chat replies, friendly email, story captions | **Colloquial written** (محاوره‌نویسی) | میشه، می‌خوام، رو، particles، fillers |
| Paper, thesis, university report, مقاله/پایان‌نامه | **Academic** (نگارش علمی) | Measured, hedged, passive OK, zero تعارف — full guide: the «Academic writing (نگارش علمی)» part |

### The detection procedure (apply in this order)

1. **Explicit instruction wins.** «رسمی بنویس»، «خودمونی باشه»، «لحن اداری» —
   obey it, whatever the document type.
2. **Deliverable type, not request tone.** Users type casually: «یه پروپوزال
   واسه مشتری بنویس» is a casual REQUEST for a formal DELIVERABLE. Classify
   the artifact, ignore the register the user typed in. This is the single
   most common detection mistake.
3. **Audience + destination.** Going to a client, organization, professor,
   or government office → formal side, even if the channel is a DM. Going to
   followers, friends, one's own team chat → casual side.
4. **One register per artifact, not per conversation.** A formal cover letter
   with casual Instagram captions attached = two artifacts, two registers.
5. **High stakes + ambiguity → ask.** If the text goes to a third party and
   signals conflict, ask ONE short question («لحن رسمی باشد یا صمیمی؟») —
   a question costs three seconds; a wrong register can cost the deal.
6. **No signal at all → formal-but-human.** It's the safe default in Persian
   professional contexts; casual by mistake is worse than formal by mistake.

Cues that flip toward casual: کپشن، استوری، پست اینستا، توییت، پیام دوستانه،
گروه دوستان، فان. Cues that flip toward formal: مشتری، سازمان، اداره، مدیر،
قرارداد، رسمی، مناقصه، دانشگاه، استاد، مقام.


<!-- lines 326,359 -->
### Formal-but-human (the register AI gets most wrong)

Formal Persian does NOT mean bureaucratic Persian. The models default to اداری
ceremony; real professional writing is closer to a smart person talking carefully:

- **است، شد، کرد** — never می‌باشد، گردید، به عمل آورد. The می‌باشد register is
  a government-office fossil; in a proposal it reads as either lazy or machine.
- Short sentences. One idea per sentence. Persian tolerates long chains of
  که-clauses; readers don't.
- Address the reader: «شما» and second-person verbs, not «کاربران محترم می‌توانند».
- Concrete over ceremonial: «سایت شما در ۳ ثانیه باز می‌شود» beats
  «بهبود چشمگیر سرعت بارگذاری را تجربه خواهید کرد».
- Warmth is allowed. تعارف is allowed in openings/closings of letters
  (یک سطر، نه یک بند). Flattery-padding is not.

**The warmth trap — «انسانی» یعنی روان، نه خودمونی.** Over-correcting away from
کتابی lands in colloquial idiom, which in a proposal or contract reads as
unprofessional to exactly the client you're trying to win. In proposals,
contracts, invoices, official letters and reports, these do NOT belong:

- Colloquial idioms: «جور بودن» (→ مناسب بودن/هم‌راستا بودن)، «ردیفه/حله»،
  «رهایتان نمی‌کنیم» (→ همراهتان می‌مانیم)، «نه آخر کار» (→ و به پایان پروژه
  موکول نمی‌شود)، «پیش خودتان می‌ماند» (→ در اختیار خودتان باقی می‌ماند)
- Spoken sentence shapes: «همین هفته یک جلسه بگذاریم» → «پیشنهاد می‌کنیم همین
  هفته جلسه‌ای کوتاه برگزار شود» — the suggestion stays, the register rises.
- Where warmth in a formal document actually comes from: short clear sentences،
  concrete numbers، direct «شما»، and ONE warm line in the closing. Not chatty
  idioms scattered through the body.

Formality slider inside this register (most → least formal): contract/invoice →
proposal/official letter → report → website copy. Website copy may borrow a
warm idiom; a proposal should not. When unsure, write the sentence formally
first and only relax it if the document type allows.


<!-- lines 405,519 -->
## Part 2: Persian AI tells — find and rewrite

These are the patterns that make Iranian readers say «اینو ربات نوشته». Scan for
every one; rewrite, don't delete — keep the meaning, lose the tell. Watch for
**clusters**: one «همچنین» is fine; همچنین + می‌باشد + «در دنیای امروز» is a confession.

### T1. می‌باشد disease (copula inflation)
The single loudest tell. Also: به شمار می‌رود، محسوب می‌شود، به حساب می‌آید،
قرار دارد (for است), گردیده است.

> ❌ وردپرس یکی از محبوب‌ترین سیستم‌های مدیریت محتوا می‌باشد و ابزاری قدرتمند محسوب می‌شود.
> ✅ وردپرس محبوب‌ترین سیستم مدیریت محتواست — قدرتش هم دقیقاً از همین‌جا می‌آید.

### T2. Ceremonial filler announcements
لازم به ذکر است که، شایان ذکر است، قابل توجه است که، همان‌طور که می‌دانید،
باید خاطرنشان کرد. Cut the announcement; say the thing.

> ❌ لازم به ذکر است که پشتیبانی به صورت ۲۴ ساعته ارائه می‌گردد.
> ✅ پشتیبانی ۲۴ ساعته است.

### T3. Significance inflation
نقش بسزایی ایفا می‌کند، از اهمیت ویژه‌ای برخوردار است، گامی مهم در راستای،
جایگاه ویژه‌ای دارد، تحولی شگرف. Replace with the concrete claim.

> ❌ سئو نقش بسزایی در موفقیت کسب‌وکار شما ایفا می‌کند.
> ✅ اگر در نتایج گوگل دیده نشوید، مشتری هم ندارید — سئو یعنی همین.

### T4. Generic openers and closers
Openers: در دنیای امروز، در عصر دیجیتال، امروزه با پیشرفت تکنولوژی، با گسترش
روزافزون اینترنت. Closers: در نهایت می‌توان گفت، به طور کلی، آینده‌ای روشن در
انتظار. Start with the actual point; end with a concrete fact or next step.

### T5. «در راستای» abuse
در راستای، در همین راستا، در جهت نیل به → usually just «برای».

### T6. Promotional emptiness
بی‌نظیر، فوق‌العاده، مثال‌زدنی، برترین، منحصربه‌فرد، تجربه‌ای متفاوت،
با کیفیتی بی‌رقیب. Specifics or silence.

> ❌ تیم ما با تجربه‌ای بی‌نظیر، خدماتی منحصربه‌فرد ارائه می‌دهد.
> ✅ در پنج سال گذشته ۴۰ پروژه تحویل داده‌ایم؛ سه‌تایشان الان روزی
> هزار سفارش دارند.

### T7. Rule of three
سریع، آسان و مطمئن؛ طراحی، توسعه و پشتیبانی — the triad rhythm is an AI
fingerprint in Persian exactly as in English. Two items, or four, or one
developed idea.

### T8. نه تنها ... بلکه (negative parallelism)
Overused. Also the clipped tail: «بدون هیچ دردسری»، «بدون نگرانی» stapled to
sentence ends. State the positive claim plainly.

### T9. Tacked-on analysis clauses (the -ing disease in Persian)
که نشان‌دهنده‌ی ... است، که بیانگر ... می‌باشد، که حاکی از ... است،
که گواهی است بر — fake depth suffixes. If the analysis matters, give it its
own sentence with evidence; usually, delete.

### T10. Vague authority
کارشناسان معتقدند، مطالعات نشان می‌دهد، تحقیقات ثابت کرده — with no named
source. Name it (طبق گزارش ۲۰۲۴ Semrush...) or drop the appeal.

### T11. False ranges
«از طراحی سایت گرفته تا سئو و تولید محتوا» when the items aren't on any scale —
just list the services.

### T12. Em dashes and English punctuation rhythm
Persian prose traditionally has no em dash; ChatGPT-style «متن — توضیح — ادامه»
is a hard tell. Use «،»، «؛»، parentheses، or a new sentence. (This file uses
one for contrast; your deliverables get zero.)

### T13. Calque phrases (translationese)
در پایان روز (at the end of the day) → آخرش، در نهایت؛
نگاهی بیندازیم به (let's take a look) → ببینیم؛
شایسته است بدانید → cut. If a phrase only exists as an English idiom's shadow,
an Iranian didn't write it.

### T14. همچنین pileup
همچنین، علاوه بر این، افزون بر آن opening consecutive sentences. Persian
connects naturally with و، هم، تازه (casual), or nothing.

### T15. Fake tanvin words
گاهاً، دوماً، ناچاراً — tanvin on Persian words is wrong (tanvin is Arabic
morphology). Use گاهی، دوم اینکه، به‌ناچار. (Real Arabic loans keep it:
واقعاً، حتماً، اصلاً، لطفاً.)

### T16. Bold-header bullet lists
The «**سرعت بالا:** توضیح» list format is ChatGPT furniture. In prose
deliverables, write paragraphs. Bullets only when the content is truly a list —
and then plain bullets, no bold-colon headers.

### T17. Sycophantic chat residue
سؤال بسیار خوبی است!، البته!، خوشحال می‌شوم کمک کنم، امیدوارم مفید بوده باشد —
chatbot correspondence pasted into content. Delete on sight.

### T18. Universal tells (from the English humanizer — they transfer)
Elegant variation (وب‌سایت/سایت/پلتفرم/پورتال cycling for one thing);
passive hiding the actor (تصمیم گرفته شد — by whom?); excessive hedging
(شاید بتوان گفت که احتمالاً); staccato manufactured drama; aphorism formulas
(«سئو زبانِ اعتماد است»); emojis decorating headings; Title Case in Latin
brand names mid-Persian is fine, but no ALL-CAPS shouting.

## Part 3: What NOT to flag

- **Correct formal Persian is not a tell.** A contract in proper formal register
  is supposed to be formal — just not می‌باشد-formal.
- **تعارف is human.** One line of «با احترام» or «قربان شما» in a letter is
  culture, not AI. Only flag stacked, empty ceremony.
- **Poetry and literary prose** play by their own rules — سعدی gets to use
  constructions a proposal can't. Don't "humanize" quoted poetry, آیات, titles,
  or proper names. Never edit inside quotations.
- **Loanwords are normal.** Iranians say آپدیت، پیج، استوری، دیجیتال مارکتینگ.
  Forcing pure-Persian coinages (تارنما for سایت) sounds weirder than the loan.
- **One همچنین, one خیلی, one exclamation** — isolated instances mean nothing.
  Look for clusters.


<!-- lines 652,800 -->
## 1. ZWNJ — نیم‌فاصله (U+200C)

The zero-width non-joiner separates morphemes *without* a visual gap while
preventing letter joining. Writing a full space (or nothing) instead is the
most common Persian typing error, and AI-generated Persian gets it wrong both
ways. In source: `‌`, HTML `&zwnj;`, or the literal character `‌`.

Required ZWNJ positions:

| Pattern | Wrong | Right |
|---|---|---|
| می/نمی + verb | می شود، نمی توانم، میشود* | می‌شود، نمی‌توانم |
| Plural ها | کتاب ها، سایت های | کتاب‌ها، سایت‌های |
| تر / ترین | بزرگ تر، مهم ترین | بزرگ‌تر، مهم‌ترین |
| Enclitic pronouns after ه | خانه ام، پروژه اش | خانه‌ام، پروژه‌اش |
| Compound prefixes | بی دقت، هم زمان | بی‌دقت، هم‌زمان |
| Compound words | وب سایت، صفحه بندی، نرم افزار | وب‌سایت، صفحه‌بندی، نرم‌افزار |
| ای after ه | حرفه ای، هفته ای | حرفه‌ای، هفته‌ای |

*میشود (fully attached) is acceptable only in colloquial register (میشه);
in formal text always می‌شود.

Lexicalized exceptions stay solid: همکار، بهتر، کمتر، بیشتر، امروزه، آنها
(آن‌ها also correct — pick one per document).

## 2. Persian characters, not Arabic

Keyboard/copy-paste contamination. These pairs look similar but are different
codepoints, break search, and render dotted/undotted wrongly:

| Use (Persian) | Never (Arabic) |
|---|---|
| ی U+06CC | ي U+064A |
| ک U+06A9 | ك U+0643 |
| ۀ/هٔ (or ه‌ی) | ة U+0629 |
| ۴۵۶ U+06F4.. | ٤٥٦ U+0664.. |

ه with hamza: خانهٔ من or خانه‌ی من — both accepted; be consistent per document.

## 3. Digits

- Persian digits ۰۱۲۳۴۵۶۷۸۹ everywhere inside Persian prose: dates
  (۱۴۰۴/۰۴/۱۷), prices (۲۵٬۰۰۰٬۰۰۰ تومان), counts, list numbers.
- Latin digits stay Latin inside: URLs, emails, phone numbers meant for
  international dialing (+98...), code, version strings (WordPress 6.5),
  file names.
- Never Arabic-Indic variants (٤ ٥ ٦).
- Percent: «۲۰٪» (U+066A) or «۲۰ درصد». In RTL both orders render fine if the
  digits are Persian; with Latin digits «20%» the run flips LTR.
- Thousands separator: ٬ (U+066C) or، comma-free spacing — one style per doc.

## 4. Punctuation

| Persian | Replaces | Note |
|---|---|---|
| ، U+060C | , | comma |
| ؛ U+061B | ; | semicolon |
| ؟ U+061F | ? | question mark |
| «...» | "..." | quotes (گیومه) |
| … | ... | ellipsis, or سه‌نقطه |

Rules:
- No space *before* punctuation, one space *after*: «درست، مثل این.»
- ! stays ! — but one, never !!!
- Em/en dashes: not used in Persian prose. Use «،» «؛» ( ) or restructure.
- Latin fragments inside Persian (brand names, code) keep Latin punctuation
  *inside the fragment*: «افزونه WooCommerce، نسخه‌ی ۹».

## 5. Ezafe (کسره‌ی اضافه)

The unwritten -e linking noun+modifier is usually implicit (کتابِ خوب → کتاب خوب).
Write it explicitly only where the host word demands it:
- After silent ه: خانه‌ی من / خانهٔ من
- After ا and و: صدای بلند، عموی من (the ی is mandatory)
- Diacritic کسره (ِ) only for disambiguation in formal/educational text.

### 5.1 هکسره — the error Iranians mock most

Two different things sound identical at the end of a word, so writers swap them.
Getting this wrong in public copy is the single fastest way to look careless:
Iranians screenshot هکسره mistakes off billboards and brand accounts for sport.

| | What it is | Written | Example |
|---|---|---|---|
| **کسره‌ی اضافه** | links a noun to what follows (ezafe) | kasre — usually left unwritten, never «ه» | کتابِ من / کتاب من |
| **«ـه» clitic** | colloquial short form of «است» (predicate) | attached «ه» | این کتابه = این کتاب است |

**The test that always works:** replace the ending with «است» and read it aloud.
If the sentence still makes sense, the correct spelling is «ـه». If it turns to
nonsense, you need a kasre (and usually write nothing at all).

- «این کتابه» ← «این کتاب است» ✓ → «ـه» correct
- «کتابه من» ← «کتاب است من» ✗ → ezafe needed: **کتابِ من** (or plain «کتاب من»)

**Wrong → right:**

| ❌ | ✅ | Why |
|---|---|---|
| کتابه من رو ندیدی؟ | کتابِ من رو ندیدی؟ | ezafe, not «است» |
| کلاسه زبان می‌رم | کلاسِ زبان می‌رم | ezafe |
| قیمته این محصول چنده؟ | قیمتِ این محصول چنده؟ | first is ezafe, second («چنده») is «است» ✓ |
| سایته شرکت بالا نمیاد | سایتِ شرکت بالا نمیاد | ezafe |
| هوا خیلی خوبِ | هوا خیلی خوبه | predicate «است» — the reverse error |
| ماشینه من خرابه | ماشینِ من خرابه | ezafe first, «است» second ✓ |

**Careful — these are NOT errors.** Many nouns simply end in ه, and they take a
normal ezafe like any other word: خانه، نامه، برنامه، پروژه، مقاله، هفته، تجربه،
شماره، بچه. «نامه شما رسید» and «پروژه‌ی شما» are both fine; nothing was swapped.

**Register note:** the «ـه» clitic belongs to colloquial writing only. In formal
or academic text write «است» in full — «این کتاب است»، not «این کتابه». So a
formal document that contains «ـه» clitics has a register problem, not just an
orthography one (see writing-style.md).

the fa_lint script (full package; chat-only AIs apply the equivalent rules manually) --check` flags probable هکسره in both directions. It reports
rather than auto-fixes, because only context decides which of two identical
sounds the writer meant — and a wrong "fix" here changes the meaning.

## 6. Spacing hygiene

- Exactly one space between words; no double spaces (common AI artifact).
- No space inside «گیومه» : «درست»، نه « غلط ».
- Parentheses: بیرون فاصله، داخل نه (مثل این).
- Latin↔Persian boundary: one space — «پلتفرم WordPress برای...».

## 7. Numbers as words

Formal prose: one-word numbers under eleven often spelled out (سه پیشنهاد،
پنج مرحله). Tables, prices, stats: always digits. Don't mix styles in one list.

## 8. Common corrections table

| Wrong | Right | Why |
|---|---|---|
| میخواهم | می‌خواهم | ZWNJ after می |
| آنها را دیدم ولی کتابها نه | آن‌ها ... کتاب‌ها | ZWNJ before ها (if using آن‌ها style) |
| عليرضا | علیرضا | Arabic ي |
| لطفا | لطفاً | tanvin on Arabic loan |
| گاهاً | گاهی | tanvin on Persian word — always wrong |
| دوماً | دوم اینکه / ثانیاً | same |
| بсمت | به سمت / به‌سمت | mashed preposition |
| "نقل قول" | «نقل قول» | گیومه |
| 20 درصد | ۲۰ درصد | Persian digits |
| سال 2026 | سال ۲۰۲۶ | Persian digits |



---


<!-- lines 960,984 -->
## 6. Specialist terminology and proper names

Applies to any field with its own vocabulary — medicine, law, finance,
engineering, design, cooking — not just technology.

- **Keep the term the field actually uses.** If practitioners and readers say
  it in English (or in an established loanword), keep that form. Inventing an
  unfamiliar Persian equivalent hurts comprehension more than the loanword
  does; forcing a purist coinage nobody uses is a translation error, not
  linguistic care.
- **Explain on first use only**, with a plain Persian explanation in
  parentheses, then use one fixed form for the rest of the text. Consistency
  beats variety here — synonym-cycling a specialist term confuses readers and
  is an AI tell (writing-style.md T18).
- **Never translate official names**: product names, menu items, buttons,
  options, form fields, legal titles, drug names, standards. Whatever the
  reader will see in front of them is what the text must say, unchanged.
- Keep the boundary between the official name and your Persian explanation
  visible, so the reader knows which words to look for.
- Write names, figures, units, dates and any codes consistently throughout —
  mixed conventions make one text look like it had several authors.
- Where a field uses commands, formulas, references or identifiers, present
  them in a fixed format and keep them LTR when they're in Latin script
  (html-css.md, docx-pdf.md).


<!-- lines 1268,1307 -->
## 1. Rules shared by every channel

- **One central topic per piece.** A post that covers two subjects gets read as
  neither.
- **The opening states the subject.** No greeting, no «در این پست می‌خواهیم...»,
  no restating the title, no rhetorical question standing in for content.
- **Never hide the answer to create suspense.** «تا آخر بخونید» is a tax on the
  reader that costs more attention than it buys.
- **Every paragraph carries one idea** and stays short enough to scan on a
  phone — without becoming a stack of disconnected fragments.
- **Critical information is never only in the image, only in the audio, or only
  behind a link.** Each surface should stand on its own to the extent it can.
- **Warnings go beside the relevant step**, not collected at the end or buried
  in a caption.
- **The closing gives the answer, the decision criterion, or the next step** —
  not a slogan and not a summary of what was just said.
- **One call to action**, with its destination and outcome named.
- **Publish-ready output only.** Internal labels like «مقدمه»، «بدنه»،
  «جمع‌بندی» are scaffolding for the writer, and must not survive into the
  posted text.

### Emoji — and why the first word after one matters in Persian

Default to no emoji. Where a channel's style uses them, they are for **semantic
separation**, not decoration: at most one (or one fixed combination) at the
start of a block, used consistently for the same meaning throughout.

There is also a genuinely technical reason to be careful. In an RTL paragraph,
an emoji is direction-neutral, so the first *strong* character after it decides
how the line is laid out. If a Latin word follows the emoji, the line can flip
to LTR and the punctuation jumps to the wrong side. **Keep the first word after
an emoji (and the first word of every paragraph) Persian**, or wrap the Latin
fragment as described in html-css.md. This is the same bidi rule that governs
Persian digits — orthography.md §3.

A workable emoji scheme, if one is wanted: numbered markers for sequence
(1️⃣ 2️⃣ 3️⃣), one consistent symbol family for risks and limits (🛑 ⚠️), another
for benefits, results and conclusions (✅ 🟢). What matters is that a symbol
means the same thing every time it appears.

