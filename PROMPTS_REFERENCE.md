# Справочник промптов Nano Banano Pro
> Этот документ сгенерирован автоматически. Не меняйте его вручную! Любые правки вносите в `prompts.json`.

## Быстрая навигация

| ID (Technical) | Название | Обязательные параметры (Args) | Описание |
|---|---|---|---|
| `upscale_restore` | **Улучшение качества (Upscale)** | `image_1` | Убирает размытость, восстанавливает детали кожи, сохраняет композицию. |
| `studio_portrait` | **Студийный портрет** | `angle`, `background`, `lighting`, `person` | Классический портрет с настройкой света и ракурса. |
| `cloth_swap` | **Замена одежды** | `image_1`, `image_2` | Меняет одежду, сохраняя позу и телосложение. |
| `object_removal` | **Удаление объекта** | `image_1`, `object` | Удаляет объект и заполняет фон (Inpainting). |
| `object_addition` | **Добавление объекта** | `image_1`, `object` | Вставляет новый объект с учетом света и теней. |
| `expression_change` | **Изменение эмоции** | `emotion`, `image_1` | Меняет мимику, сохраняя узнаваемость лица (Identity). |
| `element_combine` | **Комбинирование (Наложение)** | `element_from_image_1`, `element_from_image_2` | Наложение элемента из одного фото на другое. |
| `mockup_generation` | **Создание мокапа** | `background_type`, `object_type` | Натягивает изображение на 3D-объект (книга, девайс). |
| `sketch_to_photo` | **Скетч в Фото** | `image_1`, `materials`, `style` | Превращает набросок в реалистичное изображение. |
| `scene_composite` | **Комбинирование сцены (Composite)** | `element_1`, `element_2`, `scene_description` | Объединение элементов в единую сцену с общим балансом. |
| `text_design` | **Текстовый дизайн** | `brand`, `colors`, `design_style`, `font_style`, `graphic_type`, `text` | Генерация баннеров с читаемым текстом. |
| `logo_creative` | **Логотип (Creative)** | `colors`, `emotions`, `imagery`, `industry_brand`, `style` | Креативный дизайн логотипа с нуля. |
| `logo_food_typo` | **Стилизация логотипа (Еда)** | `food_items`, `image_1` | Логотип из продуктов питания. |
| `product_card` | **Карточка товара** | `aspect_ratio`, `features_list`, `image_1` | Инфографика для e-commerce. |
| `youtube_thumbnail` | **YouTube Обложка** | `face_description_or_image_2`, `image_1`, `text` | Замена лица и текста на превью. |
| `comic_noir` | **Нуарный комикс** | `character_description`, `situation` | Комикс в стиле Sin City. |

## Детальные шаблоны
### Улучшение качества (Upscale)
**ID:** `upscale_restore`
**Инфо:** Убирает размытость, восстанавливает детали кожи, сохраняет композицию.

```text
[RU]: Улучшить и масштабировать [image_1], сохраняя оригинальную композицию и цветовую палитру. Устранить размытость, восстановить текстуру кожи: видимые поры, микроморщины, естественный тургор. Сохранить светотеневой рисунок и фон. Повысить резкость ключевых зон (глаза, ресницы, губы, волосы). Результат — бьюти-фотография высокого разрешения, кожа без эффекта «пластика», естественная зернистость.
[EN]: Upscale and enhance [image_1], keeping composition and color palette strictly unchanged. De-blur and refine skin texture: visible pores, micro-wrinkles, and realistic subsurface scattering. Preserve original lighting and background. Sharpen key features: eyes, eyelashes, lips, and hair strands. Output as a high-end beauty photography, ultra-realistic skin texture without plastic smoothing, natural film grain.
```
---
### Студийный портрет
**ID:** `studio_portrait`
**Инфо:** Классический портрет с настройкой света и ракурса.

```text
[RU]: Профессиональный студийный портрет [person] на [background]. Ракурс: [angle]. Освещение: [lighting]. Высокая детализация, 8k.
[EN]: Professional studio portrait of [person] against [background]. Angle: [angle]. Lighting: [lighting]. Hyper-detailed, 8k resolution, sharp focus.
```
---
### Замена одежды
**ID:** `cloth_swap`
**Инфо:** Меняет одежду, сохраняя позу и телосложение.

```text
[RU]: Замените одежду персонажа на [image_1] на комплект с [image_2]. Сохраните позу, анатомию и черты лица оригинала. Перенесите текстуру ткани, складки и стиль с [image_2], обеспечив реалистичную посадку одежды на тело с учетом исходного освещения. Бесшовная интеграция.
[EN]: Replace the clothing on the character in [image_1] with the outfit from [image_2]. Strictly preserve the original pose, anatomy, and facial features. Transfer the fabric texture, folds, and style from [image_2], ensuring a realistic fit and drape on the body consistent with the original lighting. Seamless photorealistic integration.
```
---
### Удаление объекта
**ID:** `object_removal`
**Инфо:** Удаляет объект и заполняет фон (Inpainting).

```text
[RU]: Удалить [object] с [image_1]. Заполнить освободившееся пространство фоном, соответствующим окружению (текстура, освещение, глубина резкости). Сцена должна выглядеть так, будто объекта там никогда не было. Чистая композиция.
[EN]: Remove [object] from [image_1]. Inpaint the empty space to match the surrounding background (texture, lighting, depth of field). The scene must look naturally empty as if the object never existed. Clean composition, seamless blend.
```
---
### Добавление объекта
**ID:** `object_addition`
**Инфо:** Вставляет новый объект с учетом света и теней.

```text
[RU]: Вставить [object] в [image_1]. Объект должен естественно взаимодействовать с окружением: правильные тени на земле, соответствие направлению света и цветовой температуре сцены. Фотореализм.
[EN]: Insert [object] into [image_1]. The object must interact naturally with the environment: cast accurate shadows, match the direction of light, and align with the scene's color temperature. Photorealistic, seamless composite.
```
---
### Изменение эмоции
**ID:** `expression_change`
**Инфо:** Меняет мимику, сохраняя узнаваемость лица (Identity).

```text
[RU]: Изменить выражение лица персонажа на [image_1] на [emotion], сохраняя уникальные черты лица (Identity). Не менять позу, прическу, одежду и освещение. Естественная мимика, детальная проработка микровыражений.
[EN]: Change the facial expression of the person in [image_1] to [emotion], strictly preserving Facial Identity. Do not alter pose, hairstyle, clothing, or lighting. Natural mimicry, detailed micro-expressions.
```
---
### Комбинирование (Наложение)
**ID:** `element_combine`
**Инфо:** Наложение элемента из одного фото на другое.

```text
[RU]: Используя предоставленные исходники, поместите [element_from_image_2] на [element_from_image_1]. Обеспечьте физически корректное наложение (перспектива, контактные тени). Исходный объект не должен деформироваться.
[EN]: Using the provided sources, place [element_from_image_2] onto [element_from_image_1]. Ensure physically accurate layering (perspective, contact shadows). The base object must remain undeformed. High coherence.
```
---
### Создание мокапа
**ID:** `mockup_generation`
**Инфо:** Натягивает изображение на 3D-объект (книга, девайс).

```text
[RU]: Наложить изображение-обложку на 3D-мокап [object_type]. Расположить на [background_type]. Соблюсти искажение перспективы и блики на поверхности материала. Профессиональная продуктовая визуализация.
[EN]: Map this cover image onto a 3D mockup of a [object_type]. Place on a [background_type]. Respect perspective distortion and surface reflections/specularity. Professional product visualization.
```
---
### Скетч в Фото
**ID:** `sketch_to_photo`
**Инфо:** Превращает набросок в реалистичное изображение.

```text
[RU]: Преобразовать грубый набросок [image_1] в фотореалистичное изображение в стиле [style]. Строго следовать контурам и композиции скетча. Заменить штрихи на реальные текстуры материалов [materials]. Кинематографичное освещение.
[EN]: Render this rough sketch [image_1] into a photorealistic image in [style]. Strictly adhere to the sketch outlines and composition. Replace strokes with realistic material textures [materials]. Cinematic lighting, high fidelity.
```
---
### Комбинирование сцены (Composite)
**ID:** `scene_composite`
**Инфо:** Объединение элементов в единую сцену с общим балансом.

```text
[RU]: Создать композитное изображение, объединив [element_1] и [element_2]. Органично вписать объекты в единую сцену: [scene_description]. Выровнять баланс белого и уровень шума обоих исходников.
[EN]: Create a composite image by merging [element_1] and [element_2]. Organically integrate objects into a unified scene: [scene_description]. Match white balance and noise levels of both sources.
```
---
### Текстовый дизайн
**ID:** `text_design`
**Инфо:** Генерация баннеров с читаемым текстом.

```text
[RU]: Сгенерировать [graphic_type] для [brand] с четкой надписью «[text]». Шрифт: [font_style]. Стиль дизайна: [design_style]. Векторная эстетика, чистые линии, цветовая схема: [colors].
[EN]: Generate a [graphic_type] for [brand] featuring the clear text "[text]". Font: [font_style]. Design style: [design_style]. Vector aesthetics, clean lines, color scheme: [colors]. Typography focus.
```
---
### Логотип (Creative)
**ID:** `logo_creative`
**Инфо:** Креативный дизайн логотипа с нуля.

```text
[RU]: Дизайн логотипа для [industry_brand]. Эмоциональный посыл: [emotions]. Центральный образ: [imagery]. Цветовая палитра: [colors]. Стиль: [style]. Векторная графика, белый фон.
[EN]: Logo design for [industry_brand]. Emotional vibe: [emotions]. Core imagery: [imagery]. Color palette: [colors]. Style: [style]. Vector graphic, solid white background.
```
---
### Стилизация логотипа (Еда)
**ID:** `logo_food_typo`
**Инфо:** Логотип из продуктов питания.

```text
[RU]: Редизайн логотипа [image_1]: выложить форму букв, используя фотореалистичные [food_items]. Эстетика фуд-фотографии, вид сверху, мягкие тени, изолировано на белом фоне. Минимализм и читаемость.
[EN]: Redesign of logo [image_1]: construct the letterforms using photorealistic [food_items]. Food photography aesthetics, top-down view, soft shadows, isolated on white background. Minimalist and readable.
```
---
### Карточка товара
**ID:** `product_card`
**Инфо:** Инфографика для e-commerce.

```text
[RU]: Рекламная карточка товара на основе фото [image_1]. Добавить стильную инфографику с характеристиками: [features_list]. Пропорции [aspect_ratio]. Коммерческий дизайн, читаемый текст, акцент на товаре.
[EN]: E-commerce product card based on photo [image_1]. Add stylish infographics showcasing features: [features_list]. Aspect ratio [aspect_ratio]. Commercial design, readable text, product focus.
```
---
### YouTube Обложка
**ID:** `youtube_thumbnail`
**Инфо:** Замена лица и текста на превью.

```text
[RU]: Редактирование превью YouTube [image_1]: заменить лицо на [face_description_or_image_2], выполнив цветокоррекцию кожи под окружение. Заменить текст заголовка на «[text]», сохраняя оригинальный шрифт и эффекты. Остальные элементы (фон, одежда, поза) — без изменений. Высокое разрешение.
[EN]: YouTube thumbnail edit [image_1]: swap the face with [face_description_or_image_2], color-grading the skin to match the environment. Replace the title text with "[text]", preserving original font and effects. All other elements (background, clothes, pose) remain 100% unchanged. High resolution.
```
---
### Нуарный комикс
**ID:** `comic_noir`
**Инфо:** Комикс в стиле Sin City.

```text
[RU]: Страница комикса из 3 панелей. Стиль: Sin City, гранж, нуар, высокий контраст ч/б чернил. Сюжет: персонаж [character_description] в [situation]. Драматичные тени, штриховка.
[EN]: 3-panel comic page. Style: Sin City aesthetics, gritty noir, high-contrast black and white ink. Scene: character [character_description] in [situation]. Dramatic shadows, cross-hatching.
```
---