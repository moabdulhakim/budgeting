# GitHub (Workflow Guidelines)

عشان شغلنا يطلع بأحسن جودة ونوفر على نفسنا وقت ومجهود في حل الـ Conflicts، دي شوية خطوات بسيطة يا ريت كلنا نمشي عليها واحنا بنرفع الكود:

### 1. الـ Main Branch ده الأساس بتاعنا

- عشان نحافظ على استقرار السيستم دايماً، بلاش نعمل `git push` دايركت على الـ `main`.
    
- أي شغل جديد هنعمله في Branch منفصل، وبعدين نرفعه عن طريق **Pull Request (PR)**.
    
- الـ PR بيحتاج بس مراجعة و Approve من حد واحد فينا قبل ما نعمله Merge، كنوع من المراجعة السريعة مش أكتر عشان نتأكد إن الدنيا تمام.
    

### 2. تسمية البرانشات (Branch Naming)

عشان نبقى عارفين كل برانش جواه إيه من اسمه، يا ريت نستخدم التسميات دي:

- `feature/` : لو بنعمل ميزة جديدة. (مثال: `feature/reports-ui`)
    
- `bugfix/` : لو بنصلح مشكلة أو إيرور. (مثال: `bugfix/budget-calculation`)
    
- `docs/` : لو بنحدث الـ SRS أو رسومات الدياجرامز. (مثال: `docs/update-class-diagram`)
    

### 3. كتابة الـ Commits

عشان الـ History بتاعنا يبقى مقروء وواضح ونسهل على بعض المراجعة، بلاش نكتب رسايل سريعة زي `done` أو `fix`. خلينا نكتب الوصف بالشكل ده `<type>: <description>`:

- **أمثلة:**
    
    - `feat: add pie chart to reports screen`
        
    - `fix: resolve crash when navigating to empty budget`
        
    - `docs: update SRS formatting`
        

### 4. خطوات رفع الكود ببساطة (PR Lifecycle)

1. نسحب أحدث كود الأول عشان منعملش تعارض مع شغل بعض: `git pull origin main`
    
2. نفتح البرانش الجديد بتاعنا: `git checkout -b feature/your-feature-name`
    
3. نكتب الكود ونعمل Commits واضحة.
    
4. نرفع البرانش للـ Repo: `git push origin feature/your-feature-name`
    
5. نفتح PR على GitHub ونعمل Mention لأي حد في التيم عشان يبص عليه.
    

### 5. تفاصيل الـ Pull Request

واحنا بنفتح PR، يا ريت نكتب كلمتين بساط في الوصف يوضحوا:

- إيه اللي اتعمل بالظبط في التاسك دي؟
    
- إزاي اللي هيراجع يقدر يعمل Test للكود ده؟
    
- لو الـ PR ده بيحل Issue موجودة، نكتب رقمها (مثلاً `Closes #5`).
    

### 6. دمج الكود (Merge Strategy)

لما بنيجي نقبل الـ PR، هنستخدم طريقة **Squash and Merge**. دي ببساطة بتجمع كل الـ Commits اللي عملناها في البرانش وتخليهم Commit واحد منظم جوه الـ `main`، عشان شكل البروجكت يفضل مرتب وسهل نرجعله وقت التسليم.

بالتوفيق لينا جميعاً، ولو حد عنده أي اقتراح لتحسين الـ Workflow ده يقولنا! `written by gemini`
