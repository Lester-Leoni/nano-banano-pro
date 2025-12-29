# Справочник промптов Nano Banano Pro
> Этот документ сгенерирован автоматически (**2025-12-28 18:05 UTC**). Не меняйте его вручную! Любые правки вносите в `prompts.json`.

## Быстрая навигация

| ID (Technical) | Название | Обязательные параметры (Args) | Описание |
|---|---|---|---|
| `upscale_restore` | [**01. Улучшение качества (Re-Imagine)**](#upscale_restore) | `aspect_ratio`, `image_1` | Восстановление деталей без изменения сути. |
| `old_photo_restore` | [**02. Реставрация и Колоризация**](#old_photo_restore) | `aspect_ratio`, `image_1` | Восстановление старых ч/б фото: удаление царапин + цвет. |
| `studio_portrait` | [**03. Студийный портрет (High-End)**](#studio_portrait) | `aspect_ratio`, `background`, `lighting`, `person` | Портрет уровня обложки. |
| `background_change` | [**04. Замена фона (Background Change)**](#background_change) | `aspect_ratio`, `background`, `image_1` | Перенос персонажа в новое окружение/стиль. |
| `face_swap` | [**05. Замена лица (Face Swap)**](#face_swap) | `aspect_ratio`, `image_1`, `image_2` | Замена лица с сохранением сцены (только с правами/согласием). |
| `expression_change` | [**06. Изменение эмоции**](#expression_change) | `aspect_ratio`, `emotion`, `image_1`, `intensity` | Смена эмоции без потери сходства. |
| `pose_change` | [**07. Смена позы (Pose Control)**](#pose_change) | `action_description`, `aspect_ratio`, `image_1` | Перестройка сцены: новая поза для тех же персонажей. |
| `camera_angle_change` | [**08. Смена ракурса (Camera Angle)**](#camera_angle_change) | `aspect_ratio`, `camera_angle`, `image_1` | Пересъемка сцены с новой точки обзора. |
| `cloth_swap` | [**09. Виртуальная примерка (Virtual Try-On)**](#cloth_swap) | `aspect_ratio`, `fabric_material`, `image_1`, `image_2` | Замена одежды с корректной физикой ткани. |
| `object_removal` | [**10. Удаление объекта (Inpainting)**](#object_removal) | `aspect_ratio`, `image_1`, `object` | Удаление объекта с восстановлением фона. |
| `object_addition` | [**11. Добавление предмета (Object Addition)**](#object_addition) | `aspect_ratio`, `image_1`, `object`, `placement_details` | Вставка объекта с физически правдоподобными тенями. |
| `semantic_replacement` | [**12. Семантическая замена (Inpainting Swap)**](#semantic_replacement) | `aspect_ratio`, `image_1`, `new_object`, `object_to_replace` | Замена одного объекта на другой с сохранением окружения. |
| `scene_relighting` | [**13. Смена освещения (Relighting)**](#scene_relighting) | `aspect_ratio`, `image_1`, `lighting_condition` | Новый свет без изменения материалов/геометрии. |
| `total_look_builder` | [**14. Сборщик образа (Total Look)**](#total_look_builder) | `accessory_image`, `aspect_ratio`, `background`, `clothing_image`, `footwear_image`, `model_image` | Сборка полного образа: модель + одежда + обувь + аксессуар. |
| `team_composite` | [**15. Сборка команды (Team Composite)**](#team_composite) | `activity`, `aspect_ratio`, `environment`, `people_links` | Объединение разных людей в одно групповое фото. |
| `scene_composite` | [**16. Сложный фотомонтаж (Global Composite)**](#scene_composite) | `aspect_ratio`, `element_1`, `element_2`, `lens_match_mode`, `scene_description` | Сведение элементов в один правдоподобный кадр. |
| `product_card` | [**17. Карточка товара (Product Card)**](#product_card) | `aspect_ratio`, `features_list`, `image_1`, `product`, `text` | Инфографика для маркетплейсов. |
| `mockup_generation` | [**18. Генерация мокапа (Mockup)**](#mockup_generation) | `aspect_ratio`, `background_type`, `object_type`, `print_finish` | Дизайн на объекте с читаемым текстом/лого. |
| `environmental_text` | [**19. Текст в окружении (Environmental Text)**](#environmental_text) | `application_style`, `aspect_ratio`, `environment_description`, `language`, `material_type`, `target_object`, `text_content` | Фотореалистичное нанесение текста на любую поверхность (песок, камень, ткань). |
| `knolling_photography` | [**20. Кноллинг (Knolling / Flat Lay)**](#knolling_photography) | `aspect_ratio`, `background`, `object` | Аккуратная раскладка предметов сверху. |
| `logo_creative` | [**21. Логотип (Logo Creative)**](#logo_creative) | `aspect_ratio`, `brand`, `imagery`, `style` | Чистый векторный логотип. |
| `logo_stylization` | [**22. 3D Логотип (Logo Stylization)**](#logo_stylization) | `aspect_ratio`, `image_1`, `materials` | Лого, собранное из материалов/предметов. |
| `ui_design` | [**23. UI/UX Дизайн**](#ui_design) | `aspect_ratio`, `industry`, `platform`, `screen_type`, `style` | Экран приложения/сайта с аккуратной типографикой. |
| `text_design` | [**24. Типографический постер**](#text_design) | `aspect_ratio`, `colors`, `font_style`, `text` | Постер с точным воспроизведением текста. |
| `image_restyling` | [**25. Стилизация / Художники (Art Style)**](#image_restyling) | `aspect_ratio`, `image_1`, `level`, `medium`, `style` | Имитация художников (Ван Гог, Пикассо) или смена медиума (масло, скетч). |
| `sketch_to_photo` | [**26. Скетч в фото (Sketch to Photo)**](#sketch_to_photo) | `aspect_ratio`, `image_1`, `lighting`, `materials` | Фотореализм строго по линиям скетча. |
| `character_sheet` | [**27. Лист персонажа (Character Sheet)**](#character_sheet) | `aspect_ratio`, `description`, `labels_visibility` | 3 вида для 3D-референса. |
| `sticker_pack` | [**28. Набор стикеров**](#sticker_pack) | `aspect_ratio`, `character`, `count`, `list` | Стикеры с die-cut обводкой. |
| `comic_page` | [**29. Страница комикса**](#comic_page) | `aspect_ratio`, `language`, `scene`, `style` | Страница с панелями и читабельным текстом. |
| `storyboard_sequence` | [**30. Раскадровка Сцены (Storyboard)**](#storyboard_sequence) | `action_sequence`, `aspect_ratio`, `character_description`, `layout`, `scene_description`, `style` | Визуализация сценария: последовательность кадров на одном листе. |
| `seamless_pattern` | [**31. Бесшовный паттерн**](#seamless_pattern) | `aspect_ratio`, `colors`, `show_preview`, `style`, `theme` | Tileable узор для печати. |
| `interior_design` | [**32. Интерьерный дизайн**](#interior_design) | `aspect_ratio`, `materials`, `room_type`, `style` | Фотореалистичный интерьер с ровными вертикалями. |
| `architecture_exterior` | [**33. Архитектурный экстерьер**](#architecture_exterior) | `aspect_ratio`, `building_type`, `environment`, `lens`, `time` | Фотореалистичный экстерьер здания. |
| `isometric_room` | [**34. Изометрическая комната**](#isometric_room) | `aspect_ratio`, `background_color`, `room`, `style` | Изометрический cutaway без перспективного схождения. |
| `youtube_thumbnail` | [**35. Обложка YouTube (Viral)**](#youtube_thumbnail) | `expression`, `text`, `type` | Вирусное превью 16:9 (только с правами/согласием). |
| `cinematic_atmosphere` | [**36. Кинематографичная атмосфера**](#cinematic_atmosphere) | `aspect_ratio`, `style`, `subject` | Сцена "как из фильма". |
| `technical_blueprint` | [**37. Технический чертеж (Blueprint)**](#technical_blueprint) | `aspect_ratio`, `object` | Инженерная схема с размерами. |
| `exploded_view` | [**38. Взрыв-схема (Exploded View)**](#exploded_view) | `aspect_ratio`, `background`, `object`, `style` | Декомпозиция объекта на левитирующие детали. |
| `anatomical_infographic` | [**39. Анатомическая Инфографика**](#anatomical_infographic) | `aspect_ratio`, `background`, `language`, `subject` | Научный разрез: 50% внешность / 50% анатомия. |
| `macro_extreme` | [**40. Макро-съемка (Macro Extreme)**](#macro_extreme) | `aspect_ratio`, `background`, `focus_stacking`, `lighting`, `object` | Экстремальный крупный план текстур. |

## Детальные шаблоны
<a id="upscale_restore"></a>
### 01. Улучшение качества (Re-Imagine)
**ID:** `upscale_restore`
**Инфо:** Восстановление деталей без изменения сути.

```text
[RU]: Улучшить качество [image_1]: сохранить композицию/позу/лицо 1:1; восстановить микродетали и текстуру кожи (поры/пушок), убрать blur/компрессию; сохранить исходный film grain. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Enhance [image_1] without changing identity: keep composition/pose/face 1:1; restore micro-detail and natural skin texture (pores/vellus hair), remove blur/compression; retain original film grain. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="old_photo_restore"></a>
### 02. Реставрация и Колоризация
**ID:** `old_photo_restore`
**Инфо:** Восстановление старых ч/б фото: удаление царапин + цвет.

```text
[RU]: Полная реставрация старой фотографии [image_1]. Удалить дефекты (царапины, пыль, пятна, разрывы, шум), улучшить четкость и лица. Затем раскрасить (colorize) реалистично и исторически достоверно: кожа/одежда/окружение. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Full restoration of old photo [image_1]. Remove defects (scratches, dust, stains, tears, noise), enhance sharpness and facial details. Then colorize with realistic, historically accurate colors for skin/clothing/environment. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="studio_portrait"></a>
### 03. Студийный портрет (High-End)
**ID:** `studio_portrait`
**Инфо:** Портрет уровня обложки.

```text
[RU]: Студийный high-end портрет [person] на фоне/в стиле [background], свет [lighting]. Резкий фокус на глазах, мягкое боке; кожа натуральная (поры/пушок), без смены возраста и черт лица. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: High-end studio portrait of [person] with background/style [background], lighting [lighting]. Sharp eyes, soft bokeh; natural skin texture (pores/vellus hair), no face/age changes. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="background_change"></a>
### 04. Замена фона (Background Change)
**ID:** `background_change`
**Инфо:** Перенос персонажа в новое окружение/стиль.

```text
[RU]: Вырезать персонажа из [image_1] и поместить в фон/стиль [background]; совпадение света/DOF/film grain, корректный масштаб и горизонт; добавить контактную тень. Формат [aspect_ratio], 4K, sRGB. Без швов/ореолов/текста.
[EN]: Cut out the subject from [image_1] and place into background/style [background]; match lighting/DOF/film grain, correct scale and horizon; add a ground contact shadow. Format [aspect_ratio], 4K, sRGB. No seams/halos/text.
```
---
<a id="face_swap"></a>
### 05. Замена лица (Face Swap)
**ID:** `face_swap`
**Инфо:** Замена лица с сохранением сцены (только с правами/согласием).

```text
[RU]: Face swap: [image_1] = сцена/тело, [image_2] = донор. Менять только область лица; не трогать волосы/уши/контур головы/шею; сохранить взгляд/свет/тон кожи, сделать бесшовный блендинг и совпадение зерна. Формат [aspect_ratio], 4K, sRGB. Только при наличии прав/согласия.
[EN]: Face swap: [image_1] = scene/body, [image_2] = donor. Change only the facial region; keep hair/ears/head outline/neck; preserve gaze/lighting/skin tone; seamless blend with matching grain. Format [aspect_ratio], 4K, sRGB. Only with rights/consent.
```
---
<a id="expression_change"></a>
### 06. Изменение эмоции
**ID:** `expression_change`
**Инфо:** Смена эмоции без потери сходства.

```text
[RU]: Изменить эмоцию на [image_1] на [emotion] (интенсивность [intensity]); сохранить identity/наклон головы/макияж/свет; зубы не менять, если не нужна улыбка. Формат [aspect_ratio], 4K, sRGB. Без текста/артефактов.
[EN]: Change expression in [image_1] to [emotion] (intensity [intensity]); keep identity/head tilt/makeup/lighting; do not change teeth unless smiling. Format [aspect_ratio], 4K, sRGB. No text/artifacts.
```
---
<a id="pose_change"></a>
### 07. Смена позы (Pose Control)
**ID:** `pose_change`
**Инфо:** Перестройка сцены: новая поза для тех же персонажей.

```text
[RU]: Пересоздать сцену на основе [image_1]. Изменить позу персонажей на: [action_description]. КРИТИЧНО: если поза предполагает поднятие на руки, ноги поднимаемого персонажа ДОЛЖНЫ быть оторваны от земли. Сохранить лица (identity) и детали одежды. Фон и освещение — как в оригинале. Естественная анатомия и распределение веса. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Recreate the scene based on [image_1]. Change the characters' poses to: [action_description]. CRITICAL: if lifting, the subject's feet MUST be off the ground. Preserve faces (identity) and clothing details. Keep the same background and lighting. Natural anatomy and realistic weight distribution. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="camera_angle_change"></a>
### 08. Смена ракурса (Camera Angle)
**ID:** `camera_angle_change`
**Инфо:** Пересъемка сцены с новой точки обзора.

```text
[RU]: Воссоздать сцену с [image_1] с другого ракурса: [camera_angle]. Для вида сверху (top-down / bird’s-eye): камера строго над сценой, 90° overhead, ось камеры перпендикулярна полу, без линии горизонта. Сохранить идентичность персонажей, пропорции тела и детали одежды. Окружение и освещение — как в оригинале. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Recreate the scene from [image_1] from a new perspective: [camera_angle]. For top-down / bird’s-eye: camera directly above, true 90° overhead, optical axis perpendicular to the floor, no horizon line. Preserve identity, body proportions, and clothing details. Use the same environment and lighting as the original. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="cloth_swap"></a>
### 09. Виртуальная примерка (Virtual Try-On)
**ID:** `cloth_swap`
**Инфо:** Замена одежды с корректной физикой ткани.

```text
[RU]: Заменить одежду на [image_1] по референсу [image_2]; сохранить лицо/руки/волосы/аксессуары/позу; ткань [fabric_material] с реалистичными складками/натяжением и bounce light; совпадение DOF и grain. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Replace clothing on [image_1] using [image_2] reference; keep face/hands/hair/accessories/pose; fabric [fabric_material] with realistic folds/tension and bounce light; match DOF and grain. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="object_removal"></a>
### 10. Удаление объекта (Inpainting)
**ID:** `object_removal`
**Инфо:** Удаление объекта с восстановлением фона.

```text
[RU]: Удалить [object] с [image_1], включая тени/отражения/блики от него; inpaint фоном по контексту, восстановить текстуру/резкость/grain, сохранить перспективу линий. Формат [aspect_ratio], 4K, sRGB. Без швов/призраков/текста.
[EN]: Remove [object] from [image_1] including its shadows/reflections/highlights; context-aware inpaint, restore texture/sharpness/grain, preserve line perspective. Format [aspect_ratio], 4K, sRGB. No seams/ghosting/text.
```
---
<a id="object_addition"></a>
### 11. Добавление предмета (Object Addition)
**ID:** `object_addition`
**Инфо:** Вставка объекта с физически правдоподобными тенями.

```text
[RU]: Вставить [object] в [image_1] (место: [placement_details]); совпадение перспективы/масштаба/высоты камеры/DOF; отбрасываемая тень + контактная AO; совпадение WB/температуры/grain; отражение если поверхность глянцевая. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Insert [object] into [image_1] (placement: [placement_details]); match perspective/scale/camera height/DOF; cast shadow + contact AO; match WB/temperature/grain; add reflection if surface is glossy. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="semantic_replacement"></a>
### 12. Семантическая замена (Inpainting Swap)
**ID:** `semantic_replacement`
**Инфо:** Замена одного объекта на другой с сохранением окружения.

```text
[RU]: На изображении [image_1] заменить ТОЛЬКО [object_to_replace] на [new_object]. КРИТИЧНО: всё остальное (фон, пол, стены, освещение, стиль) оставить нетронутым. Новый объект должен совпадать по перспективе, масштабу, тени/контактной тени и цветовой температуре. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: In [image_1], change ONLY [object_to_replace] to [new_object]. CRITICAL: keep everything else untouched (background, lighting, style). The new object must match perspective, scale, cast shadow/contact shadow, and color temperature. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="scene_relighting"></a>
### 13. Смена освещения (Relighting)
**ID:** `scene_relighting`
**Инфо:** Новый свет без изменения материалов/геометрии.

```text
[RU]: Relight [image_1] под [lighting_condition]; сохранить геометрию и материалы (и identity людей); пересчитать тени/блики/температуру/интенсивность, не перекрашивать текстуры. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Relight [image_1] to [lighting_condition]; keep geometry/materials (and people identity); recompute shadows/highlights/temperature/intensity, do not repaint textures. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="total_look_builder"></a>
### 14. Сборщик образа (Total Look)
**ID:** `total_look_builder`
**Инфо:** Сборка полного образа: модель + одежда + обувь + аксессуар.

```text
[RU]: Создать фотореалистичный композит. Основа: [model_image]. Одежда: [clothing_image]. Обувь: [footwear_image]. Аксессуар: [accessory_image]. Объединить в один кадр с единым освещением, тенями и перспективой. Сохранить узнаваемость товаров. Фон/стиль: [background]. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Create a photorealistic composite. Base: [model_image]. Outfit: [clothing_image]. Footwear: [footwear_image]. Accessory: [accessory_image]. Merge into one frame with unified lighting, shadows, and perspective. Preserve product identity. Background/style: [background]. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="team_composite"></a>
### 15. Сборка команды (Team Composite)
**ID:** `team_composite`
**Инфо:** Объединение разных людей в одно групповое фото.

```text
[RU]: Создать реалистичное групповое фото по референсам: [people_links]. Окружение/стиль: [environment]. Сюжет/действие: [activity]. КРИТИЧНО: все персонажи в одном пространстве, корректный относительный масштаб и взаимодействие (взгляды/позы). Единое освещение, цвет и тени для всей группы. Сохранить узнаваемость лиц. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Create a realistic group photo using these references: [people_links]. Environment/style: [environment]. Action/mood: [activity]. CRITICAL: all characters share the same 3D space with correct relative scale and interaction (eye contact/poses). Unified lighting, color grading, and shadows. Preserve facial identity. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="scene_composite"></a>
### 16. Сложный фотомонтаж (Global Composite)
**ID:** `scene_composite`
**Инфо:** Сведение элементов в один правдоподобный кадр.

```text
[RU]: Собрать сцену: [element_1] + [element_2] = [scene_description]; совместить масштаб/перспективу/высоту камеры, WB/цвет, DOF, grain и контактные тени; сведение линз: [lens_match_mode]. Формат [aspect_ratio], 4K, sRGB. Без швов/ореолов/текста.
[EN]: Composite: [element_1] + [element_2] into [scene_description]; match scale/perspective/camera height, WB/color, DOF, grain and contact shadows; lens matching: [lens_match_mode]. Format [aspect_ratio], 4K, sRGB. No seams/halos/text.
```
---
<a id="product_card"></a>
### 17. Карточка товара (Product Card)
**ID:** `product_card`
**Инфо:** Инфографика для маркетплейсов.

```text
[RU]: Карточка товара [product] на основе [image_1]: продукт 50–60% кадра; текст строго "[text]" (КРИТИЧНО: не переводить и не менять символы/регистр); фичи [features_list]; безопасные поля 5–8%, читабельно на мобиле. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Product card for [product] from [image_1]: product 50–60% of frame; text exactly "[text]" (CRITICAL: do not translate or alter characters/case); features [features_list]; 5–8% safe margins, mobile readable. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="mockup_generation"></a>
### 18. Генерация мокапа (Mockup)
**ID:** `mockup_generation`
**Инфо:** Дизайн на объекте с читаемым текстом/лого.

```text
[RU]: Мокап: наложить дизайн на [object_type], фон/стиль [background_type], покрытие [print_finish]; деформация только по кривизне, текст/логотип читаемы и без ошибок. Студийный свет. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Mockup: apply design to [object_type], background/style [background_type], finish [print_finish]; warp only by curvature, text/logo readable and spelled correctly. Studio lighting. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="environmental_text"></a>
### 19. Текст в окружении (Environmental Text)
**ID:** `environmental_text`
**Инфо:** Фотореалистичное нанесение текста на любую поверхность (песок, камень, ткань).

```text
[RU]: Фотореалистичная интеграция текста "[text_content]" в сцену. Язык текста: [language] (КРИТИЧНО: не переводить и не менять символы/регистр — вывести ровно "[text_content]"). Окружение/стиль: [environment_description]. Текст нанесен на объект: [target_object] (материал: [material_type]). Способ нанесения: [application_style] (например: вышивка, гравировка, краска, надпись на песке). КРИТИЧНО: текст должен физически достоверно взаимодействовать с поверхностью — повторять её изгибы, складки, текстуру и микрорельеф. Освещение, тени и рефлексы на тексте должны полностью соответствовать условиям сцены. Формат [aspect_ratio], 4K, sRGB. Никаких водяных знаков/логотипов/лишнего текста кроме заданного.
[EN]: Photorealistic integration of text "[text_content]" into the scene. Text language: [language] (CRITICAL: do not translate or alter characters/case — render exactly "[text_content]"). Environment/style: [environment_description]. Text is applied to object: [target_object] (material: [material_type]). Application style: [application_style] (e.g., embroidery, carving, paint, writing in sand). CRITICAL: the text must physically interact with the surface authentically—following its curves, folds, texture, and micro-relief. Lighting, shadows, and reflections on the text must fully match the scene conditions. Format [aspect_ratio], 4K, sRGB. No watermarks/logos/extra text beyond the specified one.
```
---
<a id="knolling_photography"></a>
### 20. Кноллинг (Knolling / Flat Lay)
**ID:** `knolling_photography`
**Инфо:** Аккуратная раскладка предметов сверху.

```text
[RU]: Knolling [object] на фоне/в стиле [background]: строго сверху, сетка 90°, равные отступы, высокая резкость; мягкий diffused свет + лёгкая контактная тень, чтобы не "парило". Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Knolling [object] on background/style [background]: strict top-down, 90° grid, consistent spacing, high sharpness; soft diffused light + subtle contact shadow (no floating). Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="logo_creative"></a>
### 21. Логотип (Logo Creative)
**ID:** `logo_creative`
**Инфо:** Чистый векторный логотип.

```text
[RU]: Векторный логотип для [brand]: образ [imagery], стиль [style]; чистые линии, плоские формы, центр 1:1 на белом фоне, правильные отступы; текст без ошибок. Формат 1:1 (или [aspect_ratio]), 4K, sRGB.
[EN]: Vector logo for [brand]: imagery [imagery], style [style]; clean lines, flat shapes, centered 1:1 on white with clear margins; perfect spelling. Format 1:1 (or [aspect_ratio]), 4K, sRGB.
```
---
<a id="logo_stylization"></a>
### 22. 3D Логотип (Logo Stylization)
**ID:** `logo_stylization`
**Инфо:** Лого, собранное из материалов/предметов.

```text
[RU]: Логотип [image_1] из [materials]: силуэт 1:1, top-down на белом фоне, один согласованный свет, мягкие тени под объектами, фотореализм. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Logo [image_1] built from [materials]: keep silhouette 1:1, top-down on white, single coherent light, soft contact shadows, photoreal. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="ui_design"></a>
### 23. UI/UX Дизайн
**ID:** `ui_design`
**Инфо:** Экран приложения/сайта с аккуратной типографикой.

```text
[RU]: UI экран [screen_type] для [industry] ([platform]), стиль [style]; сетка 8pt и safe areas; реальный текст без ошибок, иконки единые и pixel-perfect. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: UI screen [screen_type] for [industry] ([platform]), style [style]; 8pt grid and safe areas; real copy with no spelling errors, pixel-perfect consistent icons. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="text_design"></a>
### 24. Типографический постер
**ID:** `text_design`
**Инфо:** Постер с точным воспроизведением текста.

```text
[RU]: Постер с текстом строго "[text]" (КРИТИЧНО: без изменений символов/регистра и без перевода); шрифт [font_style], аккуратный кернинг, высокая читаемость, поля 5–8%, цвета [colors]. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Poster with text exactly "[text]" (CRITICAL: no symbol/case changes and no translation); font [font_style], clean kerning, high readability, 5–8% margins, colors [colors]. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="image_restyling"></a>
### 25. Стилизация / Художники (Art Style)
**ID:** `image_restyling`
**Инфо:** Имитация художников (Ван Гог, Пикассо) или смена медиума (масло, скетч).

```text
[RU]: Трансформировать [image_1] в художественный стиль: [style] (техника: [medium]). Уровень стилизации: [level]. КРИТИЧНО: сохранить композицию и силуэты, но полностью перерисовать текстуры мазками/штрихами выбранного стиля. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Transform [image_1] into art style: [style] (technique: [medium]). Stylization level: [level]. CRITICAL: keep composition and silhouettes, but fully redraw textures with brushstrokes/hatching of the chosen style. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="sketch_to_photo"></a>
### 26. Скетч в фото (Sketch to Photo)
**ID:** `sketch_to_photo`
**Инфо:** Фотореализм строго по линиям скетча.

```text
[RU]: Рендер [image_1] в фотореализм: строго по линиям, не менять пропорции/перспективу, не добавлять новых элементов; материалы [materials], свет [lighting]. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Render [image_1] into photorealism: follow lines strictly, do not change proportions/perspective, add no new elements; materials [materials], lighting [lighting]. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="character_sheet"></a>
### 27. Лист персонажа (Character Sheet)
**ID:** `character_sheet`
**Инфо:** 3 вида для 3D-референса.

```text
[RU]: Character sheet [description]: виды Front/Side/Back, белый фон, ортографика без перспективы, единый масштаб и baseline стоп; равномерный свет; подписи: [labels_visibility]. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Character sheet [description]: Front/Side/Back views, white background, orthographic (no perspective), consistent scale and feet baseline; flat even lighting; labels: [labels_visibility]. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="sticker_pack"></a>
### 28. Набор стикеров
**ID:** `sticker_pack`
**Инфо:** Стикеры с die-cut обводкой.

```text
[RU]: Sticker pack [character], количество [count], эмоции/позы [list]; каждый стикер изолирован, единый масштаб, равные отступы; белая die-cut обводка одинаковой толщины, тёмный фон. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Sticker pack [character], count [count], emotions/poses [list]; each sticker isolated, consistent scale and spacing; thick white die-cut border, dark background. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="comic_page"></a>
### 29. Страница комикса
**ID:** `comic_page`
**Инфо:** Страница с панелями и читабельным текстом.

```text
[RU]: Страница комикса [scene]: 4–6 панелей, ровные gutters; стиль [style]; текст (если есть) на [language], читабельно и без бессмыслицы; драматичные тени по стилю. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Comic page [scene]: 4–6 panels with uniform gutters; style [style]; text (if any) in [language], legible and not gibberish; dramatic shadows per style. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="storyboard_sequence"></a>
### 30. Раскадровка Сцены (Storyboard)
**ID:** `storyboard_sequence`
**Инфо:** Визуализация сценария: последовательность кадров на одном листе.

```text
[RU]: Лист раскадровки (storyboard sheet) для сцены: [scene_description]. Компоновка: [layout] (например: сетка 2x3, 3 горизонтальных панели). Кадры показывают хронологическое развитие события: [action_sequence]. Стиль: [style] (например: быстрый скетч карандашом, кинематографичный рендер, чернильный комикс). КРИТИЧНО: персонаж [character_description] должен выглядеть одинаково во всех кадрах (visual consistency). Включить (если уместно) схематичные стрелки движения и подписи планов (Wide, Close-up). Белый фон/промежутки между панелями. Без диалогов/длинных текстов. Формат [aspect_ratio] (рекомендуется 3:2 или 16:9), 4K, sRGB. Без водяных знаков.
[EN]: Storyboard sheet for scene: [scene_description]. Layout: [layout] (e.g., 2x3 grid, 3 horizontal panels). Panels depict the chronological progression of action: [action_sequence]. Style: [style] (e.g., rough pencil sketch, cinematic render, ink comic). CRITICAL: character [character_description] must maintain visual consistency across all frames. Include (if appropriate) schematic motion arrows and shot type annotations (Wide, Close-up). White gutters/background between panels. No dialogues/long text. Format [aspect_ratio] (recommend 3:2 or 16:9), 4K, sRGB. No watermarks.
```
---
<a id="seamless_pattern"></a>
### 31. Бесшовный паттерн
**ID:** `seamless_pattern`
**Инфо:** Tileable узор для печати.

```text
[RU]: Бесшовный паттерн: тема [theme], стиль [style], цвета [colors]; края тайла стыкуются идеально (tileable), плоский 2D без перспективы/виньетки; режим: [show_preview]. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Seamless pattern: theme [theme], style [style], colors [colors]; edges match perfectly (tileable), flat 2D with no perspective/vignette; mode: [show_preview]. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="interior_design"></a>
### 32. Интерьерный дизайн
**ID:** `interior_design`
**Инфо:** Фотореалистичный интерьер с ровными вертикалями.

```text
[RU]: Интерьер [room_type], стиль [style], материалы [materials]; 24–28mm look, ровные вертикали (2-point, no keystone), естественный дневной свет, чистые текстуры и реалистичные тени. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Interior [room_type], style [style], materials [materials]; 24–28mm look, straight verticals (2-point, no keystone), natural daylight, clean textures and realistic shadows. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="architecture_exterior"></a>
### 33. Архитектурный экстерьер
**ID:** `architecture_exterior`
**Инфо:** Фотореалистичный экстерьер здания.

```text
[RU]: Экстерьер [building_type] в окружении/стиле [environment], время/погода [time]; ровные вертикали (shift lens), объектив [lens], eye-level или drone, чистые материалы и корректные тени. Формат [aspect_ratio], 4K (8K если доступно), sRGB. Без текста/водяных знаков.
[EN]: Exterior [building_type] in environment/style [environment], time/weather [time]; straight verticals (shift lens), lens look [lens], eye-level or drone, clean materials and accurate shadows. Format [aspect_ratio], 4K (8K if available), sRGB. No text/watermarks.
```
---
<a id="isometric_room"></a>
### 34. Изометрическая комната
**ID:** `isometric_room`
**Инфо:** Изометрический cutaway без перспективного схождения.

```text
[RU]: Isometric cutaway [room]: true isometric 30°/30° без схождения, стиль [style], чистые края разреза, однотонный фон [background_color], мягкий глобальный свет. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Isometric cutaway [room]: true isometric 30°/30° with no convergence, style [style], clean cut edges, solid background [background_color], soft global illumination. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="youtube_thumbnail"></a>
### 35. Обложка YouTube (Viral)
**ID:** `youtube_thumbnail`
**Инфо:** Вирусное превью 16:9 (только с правами/согласием).

```text
[RU]: YouTube thumbnail 16:9: тип [type], эмоция [expression], лицо 30–40% кадра; текст строго "[text]" (3–5 слов) (КРИТИЧНО: не переводить и не менять символы/регистр); крупный с обводкой/тенью, высокий контраст и насыщенные цвета без мелкого мусора. Формат 16:9, 4K, sRGB. Только при наличии прав/согласия. Без водяных знаков.
[EN]: YouTube thumbnail 16:9: type [type], expression [expression], face 30–40% of frame; text exactly "[text]" (3–5 words) (CRITICAL: do not translate or alter characters/case); large with stroke/shadow, high contrast and saturated colors with no tiny clutter. Format 16:9, 4K, sRGB. Only with rights/consent. No watermarks.
```
---
<a id="cinematic_atmosphere"></a>
### 36. Кинематографичная атмосфера
**ID:** `cinematic_atmosphere`
**Инфо:** Сцена "как из фильма".

```text
[RU]: Кино-сцена с [subject], стиль [style]. Свет: согласованный key light + fill/rim, дымка и volumetric rays. Эффекты мягко: mild CA, film grain, умеренные flares, cinematic grading. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Movie scene with [subject], style [style]. Lighting: coherent key + fill/rim, haze and volumetric rays. Effects kept mild: CA, film grain, restrained flares, cinematic grading. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---
<a id="technical_blueprint"></a>
### 37. Технический чертеж (Blueprint)
**ID:** `technical_blueprint`
**Инфо:** Инженерная схема с размерами.

```text
[RU]: Blueprint [object]: виды front/side/top + cross-section, ортографика; белые линии на синей сетке, единая толщина линий; размеры с единицами (mm/cm), выноски с читабельным текстом без ошибок. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Blueprint [object]: front/side/top + cross-section, orthographic; white lines on blue grid, consistent line weight; dimensions with units (mm/cm), readable annotations with correct spelling. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="exploded_view"></a>
### 38. Взрыв-схема (Exploded View)
**ID:** `exploded_view`
**Инфо:** Декомпозиция объекта на левитирующие детали.

```text
[RU]: Создать техническую взрыв-схему (exploded view) для объекта [object]. Основной объект должен быть разобран на составные части (корпус, внутренние механизмы, детали, крепежи). Все компоненты парят в воздухе, отдаляясь от центра наружу (expanded view), но строго сохраняя своё относительное расположение и ориентацию. Высокая техническая точность, отсутствие хаоса. Фон/стиль: [background] (рекомендуется белый или нейтральный студийный). Стиль визуализации: [style] (например: 3D-рендер, инженерная графика). Формат [aspect_ratio], 4K, sRGB. Без водяных знаков/текста.
[EN]: Create a technical exploded view diagram for [object]. The main object is deconstructed into its constituent parts (chassis, internal mechanisms, parts, fasteners). All components are floating in the air, expanded outward from the center, strictly maintaining their relative alignment and orientation. High technical precision, no chaos. Background/style: [background] (white or neutral studio recommended). Visualization style: [style] (e.g., 3D render, engineering illustration). Format [aspect_ratio], 4K, sRGB. No watermarks/text.
```
---
<a id="anatomical_infographic"></a>
### 39. Анатомическая Инфографика
**ID:** `anatomical_infographic`
**Инфо:** Научный разрез: 50% внешность / 50% анатомия.

```text
[RU]: Двусторонняя симметричная анатомическая иллюстрация [subject], строго фронтально. Левая половина: внешний вид. Правая половина: внутреннее строение (скелет/мышцы/механизмы). Подписи и выноски на [language]: короткие (1–3 слова), без ошибок, без бессмыслицы. Фон/стиль: [background]. Научная точность, высокая детализация. Формат [aspect_ratio], 4K, sRGB. Без водяных знаков.
[EN]: Double-sided symmetrical anatomical illustration of [subject], strict frontal view. Left half: external appearance. Right half: internal structure (skeleton/muscles/mechanisms). Labels and callouts in [language]: short (1–3 words), correct spelling, no gibberish. Background/style: [background]. Scientific accuracy, high detail. Format [aspect_ratio], 4K, sRGB. No watermarks.
```
---
<a id="macro_extreme"></a>
### 40. Макро-съемка (Macro Extreme)
**ID:** `macro_extreme`
**Инфо:** Экстремальный крупный план текстур.

```text
[RU]: Макро [object] на фоне/в стиле [background], свет [lighting]; видны микро-текстуры/пыль/неровности и капли (если нужно), очень малая DOF и сливочное боке; focus stacking: [focus_stacking]. Формат [aspect_ratio], 4K, sRGB. Без текста/водяных знаков.
[EN]: Macro [object] on background/style [background], lighting [lighting]; visible micro-texture/dust/imperfections and droplets if needed, razor-thin DOF with creamy bokeh; focus stacking: [focus_stacking]. Format [aspect_ratio], 4K, sRGB. No text/watermarks.
```
---