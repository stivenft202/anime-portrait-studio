using System.IO;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace PortraitKit
{
    /// <summary>
    /// THE CREATOR. Put it next to a <see cref="PortraitView"/>, give it the
    /// character data assets and the palette, and press Play: an on-screen
    /// panel lets you build a character with a few clicks.
    ///
    /// - Switch between the included characters (Female / Male) at the top.
    /// - Every category (hair, outfit, eyes, eye color, nose, mouth,
    ///   facial hair, hair color, skin tone, outfit color) has a &lt; and
    ///   &gt; button: one click per step,
    ///   and the portrait updates instantly. The four color categories
    ///   (eye color, hair color, skin tone, outfit color) also have a row
    ///   of clickable color swatches right under their row, so a color
    ///   can be picked in one click; the selected swatch gets a white
    ///   border.
    /// - "Randomize" (or Space) builds a whole new look at once.
    /// - "Export PNG" saves the full 1200x1600 portrait with transparency;
    ///   "Export Face PNG" saves the top 1200x1200 square.
    /// - "Save Recipe" stores the current look as a small JSON file (and
    ///   into the assigned <see cref="PortraitRecipeAsset"/>, if any), so
    ///   the exact same character can be rebuilt later with "Load Recipe"
    ///   or from your own code.
    ///
    /// Exports and recipe files go to the output folder: by default
    /// Assets/PortraitKit/Exports inside the project while in the editor,
    /// or Application.persistentDataPath/PortraitKit in a build (the
    /// status line at the bottom of the screen always shows the full
    /// path that was written).
    ///
    /// The scene is created for you by the menu
    /// "Tools &gt; Portrait Kit &gt; Create Creator Scene". Every action is
    /// also a public method, so you can drive the creator from your own UI
    /// instead of the built-in panel (set showUI to false).
    /// </summary>
    public class PortraitCreator : MonoBehaviour
    {
        [Header("View and data")]
        public PortraitView view;
        public PortraitData[] characters;
        public PortraitPalette palette;

        [Header("Recipe asset (optional)")]
        [Tooltip("When assigned, the creator starts from this recipe and " +
                 "Save Recipe also writes the look back into the asset.")]
        public PortraitRecipeAsset recipeAsset;

        [Header("On-screen panel")]
        public bool showUI = true;

        [Header("Output")]
        [Tooltip("Folder for the exported PNGs and the recipe JSON. " +
                 "Leave empty for Assets/PortraitKit/Exports in the editor " +
                 "or Application.persistentDataPath/PortraitKit in a build.")]
        public string outputFolder = "";

        /// <summary>The character data currently being edited.</summary>
        public PortraitData CurrentData
        {
            get
            {
                if (characters == null || characters.Length == 0)
                    return null;
                return characters[Mathf.Clamp(characterIndex, 0, characters.Length - 1)];
            }
        }

        /// <summary>A copy of the recipe currently on screen.</summary>
        public PortraitRecipe CurrentRecipe
        {
            get { return recipe != null ? recipe.Clone() : null; }
        }

        int characterIndex;
        PortraitRecipe recipe = new PortraitRecipe();
        string status = "";

        // Combo identification: the panel always shows the current look's
        // combo code; a look built with Randomize also gets the next
        // combo number (#1, #2, ...), like in the demo scene.
        int randomCounter;
        bool lastWasRandom;

        Text[] rowValueTexts;
        Text statusText;
        Text comboText;

        // One white-border Outline per color swatch, indexed by
        // [category][color index]; only the four color categories have
        // entries, the rest stay null. RefreshUI enables exactly the
        // outline of the currently selected color.
        Outline[][] swatchOutlines;

        // Category ids, in panel order.
        const int CatHair = 0, CatOutfit = 1, CatEyes = 2, CatEyeColor = 3, CatNose = 4, CatMouth = 5,
                  CatFacialHair = 6, CatHairColor = 7, CatSkinTone = 8, CatOutfitColor = 9, CatCount = 10;
        static readonly string[] CategoryLabels =
            { "HAIR", "OUTFIT", "EYES", "EYE COLOR", "NOSE", "MOUTH", "FACIAL HAIR", "HAIR COLOR", "SKIN TONE", "OUTFIT COLOR" };

        void Start()
        {
            if (CurrentData == null || palette == null || view == null)
            {
                SetStatus("Portrait Creator: assign a view, the characters and the palette in the Inspector.");
                if (showUI)
                    BuildUI();
                return;
            }

            characterIndex = 0;
            recipe = new PortraitRecipe { characterId = CurrentData.characterId };
            if (recipeAsset != null && recipeAsset.recipe != null)
            {
                // Start from the saved look when it belongs to one of the
                // assigned characters.
                for (int i = 0; i < characters.Length; i++)
                {
                    if (characters[i] != null && characters[i].characterId == recipeAsset.recipe.characterId)
                    {
                        characterIndex = i;
                        recipe = recipeAsset.recipe.Clone();
                        break;
                    }
                }
            }
            ClampRecipeToData();
            ApplyCurrent();
            if (showUI)
                BuildUI();
            RefreshUI();
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.Space))
                Randomize();
        }

        // ----------------------------------------------------------------
        // Character and categories
        // ----------------------------------------------------------------

        /// <summary>
        /// Switches the character being edited. Piece indices are clamped to
        /// the new character's lists: switching used to keep the old indices,
        /// so a Female hair index (up to 11) survived on Male (4 hairs) and
        /// the combo code showed "H12" while the panel showed "Style 4".
        /// </summary>
        public void SetCharacter(int index)
        {
            if (characters == null || characters.Length == 0)
                return;
            characterIndex = Mathf.Clamp(index, 0, characters.Length - 1);
            if (CurrentData != null)
                recipe.characterId = CurrentData.characterId;
            ClampRecipeToData();
            lastWasRandom = false;
            ApplyCurrent();
            RefreshUI();
        }

        /// <summary>
        /// Clamps every piece index of the current recipe to the lists of the
        /// character being edited, so the combo code, the panel names and the
        /// render always agree on the same piece. Facial hair clamps to
        /// 0..Length because 0 means None and 1..Length are the styles.
        /// </summary>
        void ClampRecipeToData()
        {
            var data = CurrentData;
            if (data == null || recipe == null)
                return;
            recipe.hairIndex = data.hairs != null && data.hairs.Length > 0
                ? Mathf.Clamp(recipe.hairIndex, 0, data.hairs.Length - 1) : 0;
            recipe.outfitIndex = data.outfits != null && data.outfits.Length > 0
                ? Mathf.Clamp(recipe.outfitIndex, 0, data.outfits.Length - 1) : 0;
            recipe.eyesIndex = data.eyes != null && data.eyes.Length > 0
                ? Mathf.Clamp(recipe.eyesIndex, 0, data.eyes.Length - 1) : 0;
            recipe.noseIndex = data.noses != null && data.noses.Length > 0
                ? Mathf.Clamp(recipe.noseIndex, 0, data.noses.Length - 1) : 0;
            recipe.mouthIndex = data.mouths != null && data.mouths.Length > 0
                ? Mathf.Clamp(recipe.mouthIndex, 0, data.mouths.Length - 1) : 0;
            recipe.facialHairIndex = data.facialHairs != null && data.facialHairs.Length > 0
                ? Mathf.Clamp(recipe.facialHairIndex, 0, data.facialHairs.Length) : 0;
        }

        /// <summary>Steps one category forward or back (wraps around).</summary>
        public void Cycle(int category, int delta)
        {
            int count = CategoryCount(category);
            if (count <= 0)
                return;
            int value = CategoryValue(category);
            value = ((value + delta) % count + count) % count;
            SetCategoryValue(category, value);
            lastWasRandom = false;
            ApplyCurrent();
            RefreshUI();
        }

        /// <summary>Picks one color directly (used by the swatch row).</summary>
        public void SelectColor(int category, int index)
        {
            int count = CategoryCount(category);
            if (count <= 0)
                return;
            SetCategoryValue(category, Mathf.Clamp(index, 0, count - 1));
            lastWasRandom = false;
            ApplyCurrent();
            RefreshUI();
        }

        /// <summary>The palette list behind a color category, or null for
        /// the piece categories (hair, outfit, eyes, nose, mouth, facial
        /// hair), which have no colors to show as swatches.</summary>
        NamedColor[] PaletteColors(int category)
        {
            if (palette == null)
                return null;
            switch (category)
            {
                case CatEyeColor: return palette.eyeColors;
                case CatHairColor: return palette.hairColors;
                case CatSkinTone: return palette.skinTones;
                case CatOutfitColor: return palette.outfitColors;
                default: return null;
            }
        }

        public void NextHair() { Cycle(CatHair, 1); }
        public void PrevHair() { Cycle(CatHair, -1); }
        public void NextOutfit() { Cycle(CatOutfit, 1); }
        public void PrevOutfit() { Cycle(CatOutfit, -1); }
        public void NextEyes() { Cycle(CatEyes, 1); }
        public void PrevEyes() { Cycle(CatEyes, -1); }
        public void NextEyeColor() { Cycle(CatEyeColor, 1); }
        public void PrevEyeColor() { Cycle(CatEyeColor, -1); }
        public void NextNose() { Cycle(CatNose, 1); }
        public void PrevNose() { Cycle(CatNose, -1); }
        public void NextMouth() { Cycle(CatMouth, 1); }
        public void PrevMouth() { Cycle(CatMouth, -1); }
        public void NextFacialHair() { Cycle(CatFacialHair, 1); }
        public void PrevFacialHair() { Cycle(CatFacialHair, -1); }
        public void NextHairColor() { Cycle(CatHairColor, 1); }
        public void PrevHairColor() { Cycle(CatHairColor, -1); }
        public void NextSkinTone() { Cycle(CatSkinTone, 1); }
        public void PrevSkinTone() { Cycle(CatSkinTone, -1); }
        public void NextOutfitColor() { Cycle(CatOutfitColor, 1); }
        public void PrevOutfitColor() { Cycle(CatOutfitColor, -1); }

        /// <summary>Builds a whole new random look for the current character.</summary>
        public void Randomize()
        {
            var data = CurrentData;
            if (data == null || palette == null)
                return;
            recipe = new PortraitRecipe
            {
                characterId = data.characterId,
                hairIndex = RandomIndex(data.hairs != null ? data.hairs.Length : 0),
                outfitIndex = RandomIndex(data.outfits != null ? data.outfits.Length : 0),
                eyesIndex = RandomIndex(data.eyes != null ? data.eyes.Length : 0),
                noseIndex = RandomIndex(data.noses != null ? data.noses.Length : 0),
                mouthIndex = RandomIndex(data.mouths != null ? data.mouths.Length : 0),
                hairColorIndex = RandomIndex(palette.hairColors != null ? palette.hairColors.Length : 0),
                skinToneIndex = RandomIndex(palette.skinTones != null ? palette.skinTones.Length : 0),
                outfitColorIndex = RandomIndex(palette.outfitColors != null ? palette.outfitColors.Length : 0),
                eyeColorIndex = RandomIndex(palette.eyeColors != null ? palette.eyeColors.Length : 0),
                facialHairIndex = data.facialHairs != null && data.facialHairs.Length > 0
                    ? RandomIndex(data.facialHairs.Length + 1) : 0,
            };
            randomCounter++;
            lastWasRandom = true;
            ApplyCurrent();
            RefreshUI();
            SetStatus("Random look applied.");
            Debug.Log("[PortraitKit] Combo #" + randomCounter + ": " +
                recipe.Describe(data, palette) + " (" + recipe.ComboCode() + ")");
        }

        int CategoryCount(int category)
        {
            var data = CurrentData;
            switch (category)
            {
                case CatHair: return data != null && data.hairs != null ? data.hairs.Length : 0;
                case CatOutfit: return data != null && data.outfits != null ? data.outfits.Length : 0;
                case CatEyes: return data != null && data.eyes != null ? data.eyes.Length : 0;
                case CatNose: return data != null && data.noses != null ? data.noses.Length : 0;
                case CatMouth: return data != null && data.mouths != null ? data.mouths.Length : 0;
                case CatHairColor: return palette != null && palette.hairColors != null ? palette.hairColors.Length : 0;
                case CatSkinTone: return palette != null && palette.skinTones != null ? palette.skinTones.Length : 0;
                case CatOutfitColor: return palette != null && palette.outfitColors != null ? palette.outfitColors.Length : 0;
                case CatEyeColor: return palette != null && palette.eyeColors != null ? palette.eyeColors.Length : 0;
                case CatFacialHair: return data != null && data.facialHairs != null ? data.facialHairs.Length + 1 : 0;
                default: return 0;
            }
        }

        int CategoryValue(int category)
        {
            switch (category)
            {
                case CatHair: return recipe.hairIndex;
                case CatOutfit: return recipe.outfitIndex;
                case CatEyes: return recipe.eyesIndex;
                case CatNose: return recipe.noseIndex;
                case CatMouth: return recipe.mouthIndex;
                case CatHairColor: return recipe.hairColorIndex;
                case CatSkinTone: return recipe.skinToneIndex;
                case CatOutfitColor: return recipe.outfitColorIndex;
                case CatEyeColor: return recipe.eyeColorIndex;
                case CatFacialHair: return recipe.facialHairIndex;
                default: return 0;
            }
        }

        void SetCategoryValue(int category, int value)
        {
            switch (category)
            {
                case CatHair: recipe.hairIndex = value; break;
                case CatOutfit: recipe.outfitIndex = value; break;
                case CatEyes: recipe.eyesIndex = value; break;
                case CatNose: recipe.noseIndex = value; break;
                case CatMouth: recipe.mouthIndex = value; break;
                case CatHairColor: recipe.hairColorIndex = value; break;
                case CatSkinTone: recipe.skinToneIndex = value; break;
                case CatOutfitColor: recipe.outfitColorIndex = value; break;
                case CatEyeColor: recipe.eyeColorIndex = value; break;
                case CatFacialHair: recipe.facialHairIndex = value; break;
            }
        }

        string CategoryName(int category)
        {
            var data = CurrentData;
            int value = CategoryValue(category);
            switch (category)
            {
                case CatHair:
                    return data != null && data.hairs != null && data.hairs.Length > 0
                        ? data.hairs[Mathf.Clamp(value, 0, data.hairs.Length - 1)].name : "-";
                case CatOutfit:
                    return data != null && data.outfits != null && data.outfits.Length > 0
                        ? data.outfits[Mathf.Clamp(value, 0, data.outfits.Length - 1)].name : "-";
                case CatEyes:
                    return data != null && data.eyes != null && data.eyes.Length > 0
                        ? data.eyes[Mathf.Clamp(value, 0, data.eyes.Length - 1)].name : "-";
                case CatNose:
                    return data != null && data.noses != null && data.noses.Length > 0
                        ? data.noses[Mathf.Clamp(value, 0, data.noses.Length - 1)].name : "-";
                case CatMouth:
                    return data != null && data.mouths != null && data.mouths.Length > 0
                        ? data.mouths[Mathf.Clamp(value, 0, data.mouths.Length - 1)].name : "-";
                case CatHairColor:
                    return palette != null && palette.hairColors != null && palette.hairColors.Length > 0
                        ? palette.hairColors[Mathf.Clamp(value, 0, palette.hairColors.Length - 1)].name : "-";
                case CatSkinTone:
                    return palette != null && palette.skinTones != null && palette.skinTones.Length > 0
                        ? palette.skinTones[Mathf.Clamp(value, 0, palette.skinTones.Length - 1)].name : "-";
                case CatOutfitColor:
                    return palette != null && palette.outfitColors != null && palette.outfitColors.Length > 0
                        ? palette.outfitColors[Mathf.Clamp(value, 0, palette.outfitColors.Length - 1)].name : "-";
                case CatEyeColor:
                    return palette != null && palette.eyeColors != null && palette.eyeColors.Length > 0
                        ? palette.eyeColors[Mathf.Clamp(value, 0, palette.eyeColors.Length - 1)].name : "-";
                case CatFacialHair:
                    if (data == null || data.facialHairs == null || data.facialHairs.Length == 0)
                        return "-";
                    return value <= 0 ? "None"
                        : data.facialHairs[Mathf.Clamp(value - 1, 0, data.facialHairs.Length - 1)].name;
                default: return "-";
            }
        }

        void ApplyCurrent()
        {
            if (view != null && CurrentData != null && palette != null)
                view.Apply(CurrentData, recipe, palette);
        }

        // ----------------------------------------------------------------
        // Export and recipe files
        // ----------------------------------------------------------------

        /// <summary>The folder where exports and recipe files are written.</summary>
        public string OutputFolderPath()
        {
            if (!string.IsNullOrEmpty(outputFolder))
                return outputFolder;
#if UNITY_EDITOR
            // Inside the editor the default output is the project
            // itself, Assets/PortraitKit/Exports: the files are easy to
            // find, appear in the Project window and travel with the
            // project's own file sync.
            return Path.Combine(Application.dataPath, "PortraitKit", "Exports");
#else
            return Path.Combine(Application.persistentDataPath, "PortraitKit");
#endif
        }

        static void RefreshEditorAssets()
        {
#if UNITY_EDITOR
            UnityEditor.AssetDatabase.Refresh();
#endif
        }

        /// <summary>Exports the full 1200x1600 portrait as a transparent PNG.</summary>
        public void ExportPng()
        {
            if (view == null || CurrentData == null)
                return;
            string path = Path.Combine(OutputFolderPath(), CurrentData.characterId + "_portrait.png");
            string error;
            if (PortraitExporter.ExportFullPng(view, path, out error))
            {
                RefreshEditorAssets();
                SetStatus("Exported: " + path);
            }
            else
                SetStatus("Export failed: " + error);
        }

        /// <summary>Exports the top 1200x1200 square (face) as a transparent PNG.</summary>
        public void ExportFacePng()
        {
            if (view == null || CurrentData == null)
                return;
            string path = Path.Combine(OutputFolderPath(), CurrentData.characterId + "_face.png");
            string error;
            if (PortraitExporter.ExportFacePng(view, path, out error))
            {
                RefreshEditorAssets();
                SetStatus("Exported: " + path);
            }
            else
                SetStatus("Export failed: " + error);
        }

        /// <summary>
        /// Saves the current look as a JSON recipe file (and into the
        /// assigned recipe asset, if any). The file is named
        /// "&lt;characterId&gt;_recipe.json" inside the output folder.
        /// </summary>
        public void SaveRecipe()
        {
            if (CurrentData == null)
                return;
            try
            {
                Directory.CreateDirectory(OutputFolderPath());
                string path = Path.Combine(OutputFolderPath(), CurrentData.characterId + "_recipe.json");
                File.WriteAllText(path, JsonUtility.ToJson(recipe, true));

                if (recipeAsset != null)
                {
                    recipeAsset.recipe = recipe.Clone();
#if UNITY_EDITOR
                    UnityEditor.EditorUtility.SetDirty(recipeAsset);
#endif
                }
                SetStatus("Recipe saved: " + path);
            }
            catch (System.Exception exception)
            {
                SetStatus("Save failed: " + exception.Message);
            }
        }

        /// <summary>
        /// Loads the recipe JSON previously saved for the current
        /// character and applies it.
        /// </summary>
        public void LoadRecipe()
        {
            if (CurrentData == null)
                return;
            string path = Path.Combine(OutputFolderPath(), CurrentData.characterId + "_recipe.json");
            if (!File.Exists(path))
            {
                SetStatus("No saved recipe found for this character yet.");
                return;
            }
            try
            {
                var loaded = JsonUtility.FromJson<PortraitRecipe>(File.ReadAllText(path));
                if (loaded == null)
                {
                    SetStatus("The saved recipe could not be read.");
                    return;
                }
                loaded.characterId = CurrentData.characterId;
                recipe = loaded;
                ClampRecipeToData();
                lastWasRandom = false;
                ApplyCurrent();
                RefreshUI();
                SetStatus("Recipe loaded: " + path);
            }
            catch (System.Exception exception)
            {
                SetStatus("Load failed: " + exception.Message);
            }
        }

        static int RandomIndex(int count)
        {
            return count > 0 ? Random.Range(0, count) : 0;
        }

        void SetStatus(string message)
        {
            status = message;
            if (!string.IsNullOrEmpty(message))
                Debug.Log("[PortraitKit] " + message);
            if (statusText != null)
                statusText.text = message;
        }

        // ----------------------------------------------------------------
        // On-screen panel (built at runtime, like the demo buttons)
        // ----------------------------------------------------------------

        void BuildUI()
        {
            if (EventSystem.current == null)
            {
                var eventSystem = new GameObject("EventSystem");
                eventSystem.AddComponent<EventSystem>();
                eventSystem.AddComponent<StandaloneInputModule>();
            }

            var canvasObject = new GameObject("PortraitKit Creator UI");
            var canvas = canvasObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            canvasObject.AddComponent<GraphicRaycaster>();

            // Panel on the right side of the screen.
            var panel = MakeRect(canvasObject.transform, 0.70f, 0.055f, 1.0f, 1.0f);
            var panelImage = panel.gameObject.AddComponent<Image>();
            panelImage.color = new Color(0.09f, 0.10f, 0.12f, 0.90f);

            var title = MakeText(panel, "PORTRAIT CREATOR", 0.04f, 0.945f, 0.96f, 0.995f, 30, TextAnchor.MiddleCenter);
            title.fontStyle = FontStyle.Bold;

            // Character buttons (one per assigned character).
            if (characters != null && characters.Length > 0)
            {
                float width = 0.92f / characters.Length;
                for (int i = 0; i < characters.Length; i++)
                {
                    int captured = i;
                    string label = characters[i] != null && !string.IsNullOrEmpty(characters[i].displayName)
                        ? characters[i].displayName : "Character " + (i + 1);
                    MakeButton(panel, label, 0.04f + i * width, 0.875f, 0.04f + (i + 1) * width - 0.01f, 0.93f,
                        () => SetCharacter(captured));
                }
            }

            // Category rows. The four color categories (eye color, hair
            // color, skin tone, outfit color) get a row of clickable
            // color swatches right under their row, so a color can be
            // picked in one click instead of stepping through the list
            // with < and >. The rows are a little shorter than before so
            // the four swatch rows fit above the action buttons.
            rowValueTexts = new Text[CatCount];
            swatchOutlines = new Outline[CatCount][];
            float rowTop = 0.868f;
            for (int c = 0; c < CatCount; c++)
            {
                int captured = c;
                float top = rowTop;
                float bottom = top - 0.038f;
                var label = MakeText(panel, CategoryLabels[c], 0.04f, bottom, 0.30f, top, 17, TextAnchor.MiddleLeft);
                label.color = new Color(0.75f, 0.78f, 0.82f);
                MakeButton(panel, "<", 0.315f, bottom, 0.415f, top, () => Cycle(captured, -1));
                rowValueTexts[c] = MakeText(panel, "-", 0.43f, bottom, 0.845f, top, 20, TextAnchor.MiddleCenter);
                MakeButton(panel, ">", 0.86f, bottom, 0.96f, top, () => Cycle(captured, 1));
                rowTop = bottom - 0.006f;

                var colors = PaletteColors(c);
                if (colors != null && colors.Length > 0)
                {
                    float swatchTop = rowTop;
                    float swatchBottom = swatchTop - 0.026f;
                    swatchOutlines[c] = new Outline[colors.Length];
                    float gap = 0.004f;
                    float w = (0.92f - gap * (colors.Length - 1)) / colors.Length;
                    for (int i = 0; i < colors.Length; i++)
                    {
                        int capturedIndex = i;
                        float x0 = 0.04f + i * (w + gap);
                        swatchOutlines[c][i] = MakeSwatch(panel, colors[i].color,
                            x0, swatchBottom, x0 + w, swatchTop,
                            () => SelectColor(captured, capturedIndex));
                    }
                    rowTop = swatchBottom - 0.006f;
                }
            }

            // Action buttons.
            string[] actions = { "Randomize", "Export PNG", "Export Face PNG", "Save Recipe", "Load Recipe" };
            UnityEngine.Events.UnityAction[] handlers =
                { Randomize, ExportPng, ExportFacePng, SaveRecipe, LoadRecipe };
            float actionTop = rowTop - 0.006f;
            for (int i = 0; i < actions.Length; i++)
            {
                float top = actionTop - i * 0.048f;
                MakeButton(panel, actions[i], 0.04f, top - 0.042f, 0.96f, top, handlers[i]);
            }

            // Combo code line at the bottom of the panel: the exact
            // recipe currently on screen, always visible in screenshots.
            comboText = MakeText(panel, "", 0.04f, 0.008f, 0.96f, 0.055f, 19, TextAnchor.MiddleCenter);
            comboText.color = new Color(1.0f, 0.88f, 0.60f);
            comboText.fontStyle = FontStyle.Bold;

            // Status strip along the bottom of the screen.
            var strip = MakeRect(canvasObject.transform, 0f, 0f, 1f, 0.045f);
            var stripImage = strip.gameObject.AddComponent<Image>();
            stripImage.color = new Color(0.09f, 0.10f, 0.12f, 0.90f);
            statusText = MakeText(strip, status, 0.01f, 0.05f, 0.99f, 0.95f, 20, TextAnchor.MiddleCenter);
        }

        void RefreshUI()
        {
            if (rowValueTexts == null)
                return;
            for (int c = 0; c < CatCount; c++)
                if (rowValueTexts[c] != null)
                    rowValueTexts[c].text = CategoryName(c);
            // The selected swatch of each color row gets a white border;
            // every other swatch has its border disabled.
            if (swatchOutlines != null)
            {
                for (int c = 0; c < CatCount; c++)
                {
                    var outlines = swatchOutlines[c];
                    if (outlines == null)
                        continue;
                    int selected = CategoryValue(c);
                    for (int i = 0; i < outlines.Length; i++)
                        if (outlines[i] != null)
                            outlines[i].enabled = (i == selected);
                }
            }
            if (statusText != null)
                statusText.text = status;
            if (comboText != null)
                comboText.text = (lastWasRandom ? "#" + randomCounter + "  " : "")
                    + recipe.ComboCode();
        }

        static RectTransform MakeRect(Transform parent, float x0, float y0, float x1, float y1)
        {
            var go = new GameObject("Rect");
            go.transform.SetParent(parent, false);
            var rect = go.AddComponent<RectTransform>();
            rect.anchorMin = new Vector2(x0, y0);
            rect.anchorMax = new Vector2(x1, y1);
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
            return rect;
        }

        static Text MakeText(Transform parent, string content, float x0, float y0, float x1, float y1,
            int fontSize, TextAnchor anchor)
        {
            var rect = MakeRect(parent, x0, y0, x1, y1);
            var text = rect.gameObject.AddComponent<Text>();
            text.text = content;
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.fontSize = fontSize;
            text.alignment = anchor;
            text.color = Color.white;
            return text;
        }

        static void MakeButton(Transform parent, string label, float x0, float y0, float x1, float y1,
            UnityEngine.Events.UnityAction onClick)
        {
            var rect = MakeRect(parent, x0, y0, x1, y1);
            rect.gameObject.name = label + " Button";
            var image = rect.gameObject.AddComponent<Image>();
            image.color = new Color(0.22f, 0.25f, 0.30f, 0.95f);
            var button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            button.onClick.AddListener(onClick);
            var text = MakeText(rect, label, 0f, 0f, 1f, 1f, 22, TextAnchor.MiddleCenter);
            text.raycastTarget = false;
            return;
        }

        /// <summary>One clickable color square. The button has no color
        /// transition, so the square always shows the exact palette color;
        /// the returned Outline (white border, starts disabled) marks the
        /// currently selected color and is toggled by RefreshUI.</summary>
        static Outline MakeSwatch(Transform parent, Color color, float x0, float y0, float x1, float y1,
            UnityEngine.Events.UnityAction onClick)
        {
            var rect = MakeRect(parent, x0, y0, x1, y1);
            rect.gameObject.name = "Swatch";
            var image = rect.gameObject.AddComponent<Image>();
            image.color = color;
            var button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            button.transition = Selectable.Transition.None;
            button.onClick.AddListener(onClick);
            var outline = rect.gameObject.AddComponent<Outline>();
            outline.effectColor = Color.white;
            outline.effectDistance = new Vector2(2f, -2f);
            outline.enabled = false;
            return outline;
        }
    }
}
