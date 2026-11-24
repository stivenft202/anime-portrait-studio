#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace PortraitKit
{
    /// <summary>
    /// One-click setup for the kit:
    /// menu "Tools &gt; Portrait Kit &gt; Create Data and Demo Scene" imports
    /// the included textures as sprites, creates the Female and Male
    /// character data and the default palette, builds the layered portrait
    /// prefab and a demo scene where both characters build themselves with
    /// random looks (press Space in Play mode for new ones).
    /// Safe to run again: existing data assets are updated in place, and an
    /// existing palette keeps its colors (they belong to the user).
    /// The Elderly (grey) layers are wired too (base, hair back/front and
    /// male facial hair): a missing Elderly file leaves its slot empty and
    /// the portrait falls back to the young layer, so the 6 transparent
    /// Female Backs (H5-H10) are intentionally not shipped.
    /// </summary>
    public static class PortraitSetupAssistant
    {
        const string Root = "Assets/PortraitKit";
        const string DataFolder = Root + "/Data";
        const string FemaleDataPath = DataFolder + "/Female.asset";
        const string MaleDataPath = DataFolder + "/Male.asset";
        const string PalettePath = DataFolder + "/DefaultPalette.asset";
        const string PrefabPath = Root + "/Prefabs/Portrait.prefab";
        const string ScenePath = Root + "/Scenes/DemoScene.unity";
        const string CreatorScenePath = Root + "/Scenes/CreatorScene.unity";

        // The layer canvases are 1200x1600 px. Imported at the default
        // 100 pixels per unit, a portrait is 12 x 16 world units.
        // The demo camera is orthographic with size 5.4, so it shows
        // 10.8 units vertically and 10.8 * 16/9 = 19.2 units horizontally
        // on a 16:9 view. At scale 0.6 a portrait is 7.2 x 9.6 units:
        // two of them (14.4 wide) fit with margin, and the height keeps
        // a 0.6 unit margin at the top and at the bottom.
        const float DemoPortraitScale = 0.6f;
        const float DemoPortraitX = 4f;
        const float DemoCameraSize = 5.4f;

        static readonly string[] EyesNames = { "Neutral", "Happy", "Sad", "Angry", "Surprised" };
        static readonly string[] EyesFiles = { "Eyes_Neutral", "Eyes_Happy", "Eyes_Sad", "Eyes_Angry", "Eyes_Surprised" };
        // The female mouths mirror the four eye moods. The male set has two
        // mouths: his Sad and Angry looks reuse the Neutral mouth, exactly
        // as the original combined expressions did.
        static readonly string[] FemaleMouthNames = { "Neutral", "Happy", "Sad", "Angry", "Surprised" };
        static readonly string[] FemaleMouthFiles = { "Mouth_Neutral", "Mouth_Happy", "Mouth_Sad", "Mouth_Angry", "Mouth_Surprised" };
        static readonly string[] MaleMouthNames = { "Neutral", "Happy", "Surprised" };
        static readonly string[] MaleMouthFiles = { "Mouth_Neutral", "Mouth_Happy", "Mouth_Surprised" };
        static readonly string[] NoseNames = { "Nose 1", "Nose 2", "Nose 3" };
        // Baked eye-color variants: one recolored eyes layer per mood and
        // color (the palette's eye colors except index 0, the original).
        static readonly string[] EyeVariantColors = { "Brown", "Blue", "Amber", "Violet", "Gray", "Red" };
        static readonly string[] FacialHairNames = { "Mustache", "Stubble", "Full Beard" };

        [MenuItem("Tools/Portrait Kit/Create Data and Demo Scene")]
        public static void CreateAll()
        {
            // --- Import the included textures as sprites ---
            string[] texturePaths = AllTexturePaths();
            foreach (string path in texturePaths)
                EnsureSpriteImport(path);

            // --- Load every sprite; abort cleanly if one is missing ---
            CharacterSprites femaleSprites = LoadCharacterSprites("Female", FemaleMouthFiles);
            CharacterSprites maleSprites = LoadCharacterSprites("Male", MaleMouthFiles);
            if (femaleSprites == null || maleSprites == null)
            {
                EditorUtility.DisplayDialog("Portrait Kit",
                    "Some kit textures are missing or could not be imported as sprites.\n" +
                    "Make sure the whole PortraitKit folder (with its Textures folder) " +
                    "is inside your project's Assets folder, then run this menu again.\n\n" +
                    "Nothing was created.", "OK");
                return;
            }

            EnsureFolder(Root + "/Data");
            EnsureFolder(Root + "/Prefabs");
            EnsureFolder(Root + "/Scenes");

            // --- Character data ---
            PortraitData female = CreateOrUpdateCharacter(FemaleDataPath, "female", "Female",
                femaleSprites,
                new[] { "Long Straight", "Pixie Cut", "Bob Cut", "Long Wavy",
                        "Twin Tails", "High Ponytail", "Long Braid", "Double Buns",
                        "Hime Cut", "Messy Bun", "Side Ponytail", "Long Curly" },
                new[] { "Sweater and Jacket", "Green Jacket", "Blue Hoodie" },
                FemaleMouthNames);
            PortraitData male = CreateOrUpdateCharacter(MaleDataPath, "male", "Male",
                maleSprites,
                new[] { "Style 1", "Style 2", "Style 3", "Style 4" },
                new[] { "Outfit 1", "Outfit 2", "Outfit 3" },
                MaleMouthNames);

            // --- Default palette (never overwrite an existing one, but
            // upgrade the legacy kit defaults in place) ---
            PortraitPalette palette = CreatePaletteIfMissing(PalettePath);
            palette = UpgradePaletteIfLegacy(palette);

            // --- Layered portrait prefab ---
            GameObject prefabRoot = BuildPrefab();
            PrefabUtility.SaveAsPrefabAsset(prefabRoot, PrefabPath);
            Object.DestroyImmediate(prefabRoot);
            AssetDatabase.SaveAssets();

            // --- Demo scene ---
            // Building the scene replaces the open one, which can pop up a
            // "save changes?" prompt. If the user cancels that prompt, stop
            // here with a clear message instead of dying halfway: the data,
            // the palette and the prefab are already created AND saved, so
            // running the menu again finishes the job.
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            {
                EditorUtility.DisplayDialog("Portrait Kit",
                    "Setup paused.\n\n" +
                    "The character data, the palette and the prefab were created " +
                    "and saved, but the demo scene was not built because the " +
                    "current scene has unsaved changes.\n\n" +
                    "Save or discard those changes, then run this menu again.", "OK");
                return;
            }
            CreateDemoScene(female, male, palette);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            // --- Verify what actually landed on disk ---
            var checkFemale = AssetDatabase.LoadAssetAtPath<PortraitData>(FemaleDataPath);
            var checkMale = AssetDatabase.LoadAssetAtPath<PortraitData>(MaleDataPath);
            bool ok = checkFemale != null && checkMale != null
                && checkFemale.baseSprite != null && checkMale.baseSprite != null
                && checkFemale.hairs != null && checkFemale.hairs.Length == 12
                && checkMale.hairs != null && checkMale.hairs.Length == 4
                && checkFemale.eyeVariants != null && checkFemale.eyeVariants.Length == 30
                && checkMale.eyeVariants != null && checkMale.eyeVariants.Length == 30
                && checkMale.facialHairs != null && checkMale.facialHairs.Length == 3
                && checkFemale.eyes != null && checkFemale.eyes.Length == 5
                && checkMale.eyes != null && checkMale.eyes.Length == 5
                && checkFemale.noses != null && checkFemale.noses.Length == 3
                && checkMale.noses != null && checkMale.noses.Length == 3
                && checkFemale.mouths != null && checkFemale.mouths.Length == 5
                && checkMale.mouths != null && checkMale.mouths.Length == 3;
            if (!ok)
            {
                EditorUtility.DisplayDialog("Portrait Kit",
                    "Setup finished, but the character data could not be verified.\n\n" +
                    "Select Assets/PortraitKit/Data/Female: its Character Id should " +
                    "read \"female\" and its lists should be filled. If it reads " +
                    "\"character\" with empty lists, delete the PortraitKit/Data " +
                    "folder and run this menu again.", "OK");
                return;
            }

            EditorUtility.DisplayDialog("Portrait Kit",
                "Portrait Kit is ready.\n\n" +
                "Created or updated:\n" +
                "- " + FemaleDataPath + "\n" +
                "- " + MaleDataPath + "\n" +
                "- " + PalettePath + "\n" +
                "- " + PrefabPath + "\n" +
                "- " + ScenePath + "\n\n" +
                "Open the demo scene and press Play: both characters build " +
                "themselves with a random look. Press Space for new ones.", "OK");
        }

        [MenuItem("Tools/Portrait Kit/Create Creator Scene")]
        public static void CreateCreatorScene()
        {
            var female = AssetDatabase.LoadAssetAtPath<PortraitData>(FemaleDataPath);
            var male = AssetDatabase.LoadAssetAtPath<PortraitData>(MaleDataPath);
            var palette = AssetDatabase.LoadAssetAtPath<PortraitPalette>(PalettePath);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
            if (female == null || male == null || palette == null || prefab == null)
            {
                EditorUtility.DisplayDialog("Portrait Kit",
                    "Run \"Tools > Portrait Kit > Create Data and Demo Scene\" first: " +
                    "the creator scene needs the character data, the palette and " +
                    "the prefab it creates.", "OK");
                return;
            }

            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                return;

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            Camera camera = Camera.main;
            if (camera != null)
            {
                camera.orthographic = true;
                camera.orthographicSize = DemoCameraSize;
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = new Color(0.13f, 0.15f, 0.18f); // dark slate
            }

            var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
            instance.name = "Portrait_Creator";
            // The creator panel takes the right 30% of the screen, so the
            // portrait stands left of center.
            instance.transform.position = new Vector3(-3.4f, 0f, 0f);
            instance.transform.localScale = Vector3.one * DemoPortraitScale;

            var creatorGO = new GameObject("Creator");
            var creator = creatorGO.AddComponent<PortraitCreator>();
            creator.view = instance.GetComponent<PortraitView>();
            creator.characters = new[] { female, male };
            creator.palette = palette;

            EditorSceneManager.SaveScene(scene, CreatorScenePath);
            EditorSceneManager.OpenScene(CreatorScenePath);

            EditorUtility.DisplayDialog("Portrait Kit",
                "Creator scene ready.\n\n" +
                "Open " + CreatorScenePath + " and press Play: switch between " +
                "Female and Male at the top of the panel, step through hair, " +
                "outfit, eyes, nose, mouth and colors with the < and > buttons, " +
                "and use the action buttons to randomize, export PNGs and save " +
                "the recipe of your character.", "OK");
        }

        [MenuItem("Tools/Portrait Kit/Create Character Data")]
        public static void CreateData()
        {
            EnsureFolder(DataFolder);
            var data = ScriptableObject.CreateInstance<PortraitData>();
            string path = AssetDatabase.GenerateUniqueAssetPath(DataFolder + "/NewPortrait.asset");
            AssetDatabase.CreateAsset(data, path);
            AssetDatabase.SaveAssets();
            Selection.activeObject = data;
            EditorGUIUtility.PingObject(data);
        }

        // ----------------------------------------------------------------
        // Texture import and loading
        // ----------------------------------------------------------------

        static string[] AllTexturePaths()
        {
            var paths = new System.Collections.Generic.List<string>();
            foreach (string character in new[] { "Female", "Male" })
            {
                string folder = Root + "/Textures/" + character;
                paths.Add(folder + "/Base.png");
                int hairCount = character == "Female" ? 12 : 4;
                for (int i = 1; i <= hairCount; i++)
                {
                    paths.Add(folder + "/Hair" + i + "_Back.png");
                    paths.Add(folder + "/Hair" + i + "_Front.png");
                }
                // Elderly (grey) versions of the same layers, fully grey
                // baked. Missing files are fine: EnsureSpriteImport skips
                // them (the 6 transparent Female Backs H5-H10 are not
                // shipped on purpose; those slots stay empty).
                paths.Add(folder + "/Base_Elderly.png");
                for (int i = 1; i <= hairCount; i++)
                {
                    paths.Add(folder + "/Hair" + i + "_Back_Elderly.png");
                    paths.Add(folder + "/Hair" + i + "_Front_Elderly.png");
                }
                for (int i = 1; i <= 3; i++)
                    paths.Add(folder + "/Outfit" + i + ".png");
                foreach (string file in EyesFiles)
                    paths.Add(folder + "/" + file + ".png");
                foreach (string file in EyesFiles)
                    foreach (string colorName in EyeVariantColors)
                        paths.Add(folder + "/EyesColor_" + file.Substring(5) + "_" + colorName + ".png");
                if (character == "Male")
                    for (int i = 1; i <= 3; i++)
                        paths.Add(folder + "/FacialHair" + i + ".png");
                if (character == "Male")
                    for (int i = 1; i <= 3; i++)
                        paths.Add(folder + "/FacialHair" + i + "_Elderly.png");
                paths.Add(folder + "/Nose1.png");
                paths.Add(folder + "/Nose2.png");
                paths.Add(folder + "/Nose3.png");
                string[] mouthFiles = character == "Female" ? FemaleMouthFiles : MaleMouthFiles;
                foreach (string file in mouthFiles)
                    paths.Add(folder + "/" + file + ".png");
            }
            return paths.ToArray();
        }

        static void EnsureSpriteImport(string path)
        {
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null)
                return;
            bool changed = false;
            if (importer.textureType != TextureImporterType.Sprite)
            {
                importer.textureType = TextureImporterType.Sprite;
                changed = true;
            }
            if (importer.spriteImportMode != SpriteImportMode.Single)
            {
                importer.spriteImportMode = SpriteImportMode.Single;
                changed = true;
            }
            if (!importer.alphaIsTransparency)
            {
                importer.alphaIsTransparency = true;
                changed = true;
            }
            if (changed)
                importer.SaveAndReimport();
        }

        /// <summary>The sprites of one character, grouped by category.</summary>
        class CharacterSprites
        {
            public Sprite baseSprite;
            public Sprite[] hairBacks;
            public Sprite[] hairFronts;
            // Elderly (grey) versions. Optional on purpose: a missing file
            // leaves the slot null and the portrait falls back to the young
            // layer. They are NOT part of Complete (the 6 transparent
            // Female Backs H5-H10 are not shipped).
            public Sprite baseElderlySprite;
            public Sprite[] hairBacksElderly;
            public Sprite[] hairFrontsElderly;
            public Sprite[] facialHairsElderly = new Sprite[0];
            public Sprite[] outfits = new Sprite[3];
            public Sprite[] eyes = new Sprite[5];
            public Sprite[] eyeVariants = new Sprite[30];
            public Sprite[] facialHairs = new Sprite[0];
            public Sprite[] noses = new Sprite[3];
            public Sprite[] mouths;

            public bool Complete
            {
                get
                {
                    if (baseSprite == null || mouths == null)
                        return false;
                    foreach (var list in new[] { hairBacks, hairFronts, outfits, eyes, eyeVariants, facialHairs, noses, mouths })
                        foreach (Sprite sprite in list)
                            if (sprite == null)
                                return false;
                    return true;
                }
            }
        }

        /// <summary>
        /// Loads every sprite of one character (base, 4 hairstyles, 3
        /// outfits, 5 eyes, 3 noses and the character's mouths). Returns
        /// null if any sprite is missing.
        /// </summary>
        static CharacterSprites LoadCharacterSprites(string character, string[] mouthFiles)
        {
            string folder = Root + "/Textures/" + character;
            var result = new CharacterSprites();
            result.baseSprite = LoadSprite(folder + "/Base.png");
            int hairCount = character == "Female" ? 12 : 4;
            result.hairBacks = new Sprite[hairCount];
            result.hairFronts = new Sprite[hairCount];
            for (int i = 0; i < hairCount; i++)
            {
                result.hairBacks[i] = LoadSprite(folder + "/Hair" + (i + 1) + "_Back.png");
                result.hairFronts[i] = LoadSprite(folder + "/Hair" + (i + 1) + "_Front.png");
            }
            // Elderly (grey) versions; a missing file loads as null and the
            // portrait falls back to the young layer.
            result.baseElderlySprite = LoadSprite(folder + "/Base_Elderly.png");
            result.hairBacksElderly = new Sprite[hairCount];
            result.hairFrontsElderly = new Sprite[hairCount];
            for (int i = 0; i < hairCount; i++)
            {
                result.hairBacksElderly[i] = LoadSprite(folder + "/Hair" + (i + 1) + "_Back_Elderly.png");
                result.hairFrontsElderly[i] = LoadSprite(folder + "/Hair" + (i + 1) + "_Front_Elderly.png");
            }
            for (int i = 0; i < 3; i++)
                result.outfits[i] = LoadSprite(folder + "/Outfit" + (i + 1) + ".png");
            for (int i = 0; i < EyesFiles.Length; i++)
                result.eyes[i] = LoadSprite(folder + "/" + EyesFiles[i] + ".png");
            for (int e = 0; e < EyesFiles.Length; e++)
                for (int c = 0; c < EyeVariantColors.Length; c++)
                    result.eyeVariants[e * EyeVariantColors.Length + c] = LoadSprite(
                        folder + "/EyesColor_" + EyesFiles[e].Substring(5) + "_" + EyeVariantColors[c] + ".png");
            if (character == "Male")
            {
                result.facialHairs = new Sprite[FacialHairNames.Length];
                for (int i = 0; i < FacialHairNames.Length; i++)
                    result.facialHairs[i] = LoadSprite(folder + "/FacialHair" + (i + 1) + ".png");
            }
            if (character == "Male")
            {
                result.facialHairsElderly = new Sprite[FacialHairNames.Length];
                for (int i = 0; i < FacialHairNames.Length; i++)
                    result.facialHairsElderly[i] = LoadSprite(folder + "/FacialHair" + (i + 1) + "_Elderly.png");
            }
            for (int i = 0; i < 3; i++)
                result.noses[i] = LoadSprite(folder + "/Nose" + (i + 1) + ".png");
            result.mouths = new Sprite[mouthFiles.Length];
            for (int i = 0; i < mouthFiles.Length; i++)
                result.mouths[i] = LoadSprite(folder + "/" + mouthFiles[i] + ".png");

            return result.Complete ? result : null;
        }

        static Sprite LoadSprite(string path)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        // ----------------------------------------------------------------
        // Data assets
        // ----------------------------------------------------------------

        static PortraitData CreateOrUpdateCharacter(string path, string characterId,
            string displayName, CharacterSprites sprites, string[] hairNames,
            string[] outfitNames, string[] mouthNames)
        {
            var data = AssetDatabase.LoadAssetAtPath<PortraitData>(path);
            bool isNew = data == null;
            if (isNew)
                data = ScriptableObject.CreateInstance<PortraitData>();

            // Fill EVERYTHING before the asset touches the disk, then save
            // immediately: an asset created first and filled later stays
            // with its default empty values on disk if anything interrupts
            // the setup before the final save.
            data.characterId = characterId;
            data.displayName = displayName;
            data.baseSprite = sprites.baseSprite;
            data.baseElderlySprite = sprites.baseElderlySprite;

            data.hairs = new HairStyle[sprites.hairBacks.Length];
            for (int i = 0; i < sprites.hairBacks.Length; i++)
            {
                data.hairs[i] = new HairStyle
                {
                    name = hairNames[i],
                    backSprite = sprites.hairBacks[i],
                    frontSprite = sprites.hairFronts[i],
                    backElderlySprite = sprites.hairBacksElderly[i],
                    frontElderlySprite = sprites.hairFrontsElderly[i],
                };
            }

            data.outfits = new NamedSprite[3];
            for (int i = 0; i < 3; i++)
                data.outfits[i] = new NamedSprite { name = outfitNames[i], sprite = sprites.outfits[i] };

            data.eyes = new NamedSprite[5];
            for (int i = 0; i < 5; i++)
                data.eyes[i] = new NamedSprite { name = EyesNames[i], sprite = sprites.eyes[i] };

            data.eyeVariants = new NamedSprite[sprites.eyeVariants.Length];
            for (int e = 0; e < EyesNames.Length; e++)
                for (int c = 0; c < EyeVariantColors.Length; c++)
                    data.eyeVariants[e * EyeVariantColors.Length + c] = new NamedSprite
                    {
                        name = EyesNames[e] + "|" + EyeVariantColors[c],
                        sprite = sprites.eyeVariants[e * EyeVariantColors.Length + c],
                    };

            data.facialHairs = new NamedSprite[sprites.facialHairs.Length];
            for (int i = 0; i < sprites.facialHairs.Length; i++)
                data.facialHairs[i] = new NamedSprite { name = FacialHairNames[i], sprite = sprites.facialHairs[i] };

            data.facialHairsElderly = new NamedSprite[sprites.facialHairsElderly.Length];
            for (int i = 0; i < sprites.facialHairsElderly.Length; i++)
                data.facialHairsElderly[i] = new NamedSprite { name = FacialHairNames[i], sprite = sprites.facialHairsElderly[i] };

            data.noses = new NamedSprite[3];
            for (int i = 0; i < 3; i++)
                data.noses[i] = new NamedSprite { name = NoseNames[i], sprite = sprites.noses[i] };

            data.mouths = new NamedSprite[mouthNames.Length];
            for (int i = 0; i < mouthNames.Length; i++)
                data.mouths[i] = new NamedSprite { name = mouthNames[i], sprite = sprites.mouths[i] };

            if (isNew)
                AssetDatabase.CreateAsset(data, path);
            EditorUtility.SetDirty(data);
            AssetDatabase.SaveAssets();
            return data;
        }

        // Palettes created by older versions of the kit carry the legacy
        // defaults (6 hair colors, 6 outfit colors, 5 reserved eye
        // colors). Those were kit defaults, never user art: upgrade them
        // in place to the current defaults. A palette with any other
        // signature is the user's own work and is left untouched.
        static PortraitPalette UpgradePaletteIfLegacy(PortraitPalette palette)
        {
            if (palette == null)
                return palette;
            bool legacy = palette.hairColors != null && palette.hairColors.Length == 6
                && palette.outfitColors != null && palette.outfitColors.Length == 6
                && palette.eyeColors != null && palette.eyeColors.Length == 5;
            if (!legacy)
                return palette;
            var fresh = ScriptableObject.CreateInstance<PortraitPalette>();
            palette.hairColors = fresh.hairColors;
            palette.outfitColors = fresh.outfitColors;
            palette.eyeColors = fresh.eyeColors;
            Object.DestroyImmediate(fresh);
            EditorUtility.SetDirty(palette);
            AssetDatabase.SaveAssets();
            return palette;
        }

        static PortraitPalette CreatePaletteIfMissing(string path)
        {
            var palette = AssetDatabase.LoadAssetAtPath<PortraitPalette>(path);
            if (palette != null)
                return palette; // the colors belong to the user: never overwrite
            palette = ScriptableObject.CreateInstance<PortraitPalette>();
            AssetDatabase.CreateAsset(palette, path);
            EditorUtility.SetDirty(palette);
            AssetDatabase.SaveAssets();
            return palette;
        }

        // ----------------------------------------------------------------
        // Prefab and demo scene
        // ----------------------------------------------------------------

        static GameObject BuildPrefab()
        {
            var root = new GameObject("Portrait");
            var view = root.AddComponent<PortraitView>();
            view.hairBackRenderer = CreateLayer(root.transform, "HairBack", 10);
            view.baseRenderer = CreateLayer(root.transform, "Base", 20);
            view.outfitRenderer = CreateLayer(root.transform, "Outfit", 30);
            view.noseRenderer = CreateLayer(root.transform, "Nose", 35);
            view.eyesRenderer = CreateLayer(root.transform, "Eyes", 40);
            view.mouthRenderer = CreateLayer(root.transform, "Mouth", 45);
            view.facialHairRenderer = CreateLayer(root.transform, "FacialHair", 47);
            view.hairFrontRenderer = CreateLayer(root.transform, "HairFront", 50);
            view.accessoryRenderer = CreateLayer(root.transform, "Accessory", 60);
            return root;
        }

        static SpriteRenderer CreateLayer(Transform parent, string name, int sortingOrder)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sortingOrder = sortingOrder;
            return renderer;
        }

        static void CreateDemoScene(PortraitData female, PortraitData male, PortraitPalette palette)
        {
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            Camera camera = Camera.main;
            if (camera != null)
            {
                camera.orthographic = true;
                camera.orthographicSize = DemoCameraSize;
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = new Color(0.13f, 0.15f, 0.18f); // dark slate
            }

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);

            var femaleInstance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
            femaleInstance.name = "Portrait_Female";
            femaleInstance.transform.position = new Vector3(-DemoPortraitX, 0f, 0f);
            femaleInstance.transform.localScale = Vector3.one * DemoPortraitScale;

            var maleInstance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
            maleInstance.name = "Portrait_Male";
            maleInstance.transform.position = new Vector3(DemoPortraitX, 0f, 0f);
            maleInstance.transform.localScale = Vector3.one * DemoPortraitScale;

            var demoGO = new GameObject("Demo");
            var demo = demoGO.AddComponent<PortraitDemo>();
            demo.femaleView = femaleInstance.GetComponent<PortraitView>();
            demo.maleView = maleInstance.GetComponent<PortraitView>();
            demo.femaleData = female;
            demo.maleData = male;
            demo.palette = palette;

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorSceneManager.OpenScene(ScenePath);
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path))
                return;
            string parent = path.Substring(0, path.LastIndexOf('/'));
            string name = path.Substring(path.LastIndexOf('/') + 1);
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, name);
        }
    }
}
#endif
