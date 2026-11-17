# Arabic CDA Annotation: Reproducibility Toolkit

## الغرض / Scope
حزمة عامة لفهم مخطط توسيم الخطاب العربي بأربعة مستويات، وتشغيل توسيم جديد، والتحقق من صحة الوسوم وحساب التكرارات والاتفاق عند توفير بيانات محكّمين. المراجع النظرية: Fairclough (1992); van Dijk (1993, 1998); Wodak & Meyer (2001); Halliday & Matthiessen (2014); van Leeuwen (2007).

**مهم للتوثيق:** هذه الحزمة أُعيد إعدادها من ملفات المخطط والمخرجات المحفوظة لمساعدة الآخرين على تكرار طريقة العمل؛ وهي ليست ادعاءً بأن كل سطر من الكود أو نص التعليمات هو الملف التاريخي نفسه الذي شغّل التجربة. يجب توثيق نسخة النموذج الفعلية وسجل استدعاءاته بصورة مستقلة عند النشر.

### المحتويات
- `annotation_taxonomy.json`: 146 وسمًا مع التعريفات العربية المستخرجة من ملف المخطط المرفق (29 أيديولوجيًا، 27 تركيبيًا، 39 وظيفيًا، 51 خطابيًا)
- `prompt_ar.md`: نص تعليمات علمي مقترح للإعادة، وليس نسخة مؤرخة من البرومبت الأصلي
- `annotate_pipeline.py`: استقبال ملفات DOCX، المعالجة التتابعية، الحفظ لكل فقرة، التحقق من الوسوم، واستئناف العمل
- `audit_annotations.py`: تكرارات الوسوم، حالات `Unspecified`، وعدد وسوم خارج المخطط، وفهرس المواضع
- `agreement_metrics.py`: التطابق المباشر وآليات الاتفاق بين الأزواج والاتفاق متعدد المحكّمين عند توفر ملفاتهم
- `data/example.json`: مثال اصطناعي غير مأخوذ من مدونة الدراسة

### التثبيت
```bash
python -m pip install -r requirements.txt
```

### تشغيل توسيم فقرة DOCX
```bash
export OPENAI_API_KEY='YOUR_OWN_KEY'    # Linux / macOS
# Windows PowerShell: $env:OPENAI_API_KEY='YOUR_OWN_KEY'
python annotate_pipeline.py --input "example.docx" --model gpt-4o --output outputs/example_labeled.json
```

### الإحصاء الدقيق من JSON
```bash
python audit_annotations.py --files outputs/example_labeled.json --out outputs/audit
```
يمكن تمرير عدة ملفات في وسيطة `--files`. لا يمزج البرنامج بين التسميات غير المتكافئة نظريًا، ولا يجمع مستويات مختلفة دون التصريح بذلك.

### اتفاق المحكّمين
مدخل `agreement_metrics.py` ملف CSV برؤوس `item_id,level,reviewer,labels`، حيث `labels` قائمة JSON من الوسوم الخاصة بالمحكّم؛ تُضاف صفوف الآلة باسم `AUTO`، وتُستعمل أسماء متمايزة للبشر. يلزم اشتراك المحكّمين في الوحدات نفسها لحساب اتفاق الأزواج. معاملات كابا وألفا تختلف عن نسبة التطابق البسيطة.
```bash
python agreement_metrics.py --input reviewers.csv --out outputs/agreement
```

### خصوصية البيانات وإعادة الإنتاج
لا تتضمن الحزمة **النصوص السياسية الأصلية، أو أحكام المحكّمين، أو مفاتيح API**. هذه البيانات لا تُنشر إلا بعد موافقة أصحاب الحقوق والتصريح بإتاحتها. يجب عدم وضع المفاتيح أو بيانات المحكّمين الشخصية في GitHub/OSF. ويجب عدم الادعاء بأن درجة ثقة مولدة ذاتيًا تساوي احتمالًا معايرًا.

### Disclosure
The code and prompt are a newly constructed reproducibility implementation informed by the source files, not a verbatim historical artifact. Model aliases may change; record the `response.model`, request ID, and UTC timestamp at runtime for future studies.
