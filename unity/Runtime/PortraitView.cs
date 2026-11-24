using UnityEngine;

namespace PortraitKit
{
    /// <summary>
    /// Stacks the layers of one character and shows the finished portrait.
    /// Every layer is a full 1200x1600 canvas, so the layers always align;
    /// the renderers only differ in sprite, tint color and sorting order.
    ///
    /// Layer order (back to front, fixed sorting orders):
    /// HairBack 10, Base 20, Outfit 30, Nose 35, Eyes 40, Mouth 45,
    /// FacialHair 47, HairFront 50, Accessory 60.
    ///
    /// IMPORTANT: the face features live in SEPARATE layers (eyes, nose,
    /// mouth), so they can be combined freely. The eyes and mouth
    /// renderers are NEVER tinted (always white); the nose follows the
    /// skin tone, because its artwork is skin shading. Eye colors swap
    /// the eyes layer for a baked variant with a recolored iris, and
    /// the male character's facial hair is tinted with the hair color.
    ///
    /// The portrait prefab is created for you by the menu
    /// "Tools &gt; Portrait Kit &gt; Create Data and Demo Scene".
    ///
    /// AGE: when the recipe's age is Elderly, the view shows the
    /// character's elderly base (PortraitData.baseElderlySprite) and the
    /// grey v11 hair layers (HairStyle back/frontElderlySprite) with NO
    /// hair tint; missing elderly sprites fall back to the young ones.
    /// Facial hair has no elderly version and keeps its normal layer
    /// and hair-color tint. See unity/EDAD_TEXTURAS.md for the mapping.
    /// </summary>
    public class PortraitView : MonoBehaviour
    {
        [Header("Layer renderers (back to front)")]
        public SpriteRenderer hairBackRenderer;
        public SpriteRenderer baseRenderer;
        public SpriteRenderer outfitRenderer;
        public SpriteRenderer noseRenderer;
        public SpriteRenderer eyesRenderer;
        public SpriteRenderer mouthRenderer;
        public SpriteRenderer facialHairRenderer;
        public SpriteRenderer hairFrontRenderer;
        public SpriteRenderer accessoryRenderer;

        [Header("Data shown at start (optional)")]
        public PortraitData data;
        public PortraitPalette palette;

        /// <summary>The character data currently applied (null if none).</summary>
        public PortraitData CurrentData { get; private set; }

        /// <summary>The recipe currently applied (null if none).</summary>
        public PortraitRecipe CurrentRecipe { get; private set; }

        /// <summary>The palette currently applied (null if none).</summary>
        public PortraitPalette CurrentPalette { get; private set; }

        void Awake()
        {
            FixSortingOrders();
        }

        void Start()
        {
            // Optional auto-start: with data and palette assigned in the
            // Inspector, show the character with the default recipe.
            if (data != null && palette != null && CurrentData == null)
            {
                var recipe = new PortraitRecipe { characterId = data.characterId };
                Apply(data, recipe, palette);
            }
        }

        /// <summary>
        /// Rebuilds the whole portrait from the given data, recipe and
        /// palette. Out-of-range indices are clamped, nulls are tolerated.
        /// When the recipe's age is Elderly (ageIndex 1) the elderly base
        /// and the grey v11 hair layers are used instead of the young ones,
        /// and the hair is NOT tinted (the grey is baked in the layer);
        /// missing elderly sprites fall back to the young ones.
        /// </summary>
        public void Apply(PortraitData newData, PortraitRecipe recipe, PortraitPalette newPalette)
        {
            CurrentData = newData;
            CurrentPalette = newPalette;
            if (newData == null || recipe == null)
            {
                CurrentRecipe = recipe;
                return;
            }

            CurrentRecipe = recipe.Clone();
            CurrentRecipe.characterId = newData.characterId;

            if (baseRenderer != null)
                baseRenderer.sprite = ElderlyBase(newData, CurrentRecipe.ageIndex);

            SetHair(CurrentRecipe.hairIndex);
            SetOutfit(CurrentRecipe.outfitIndex);
            SetNose(CurrentRecipe.noseIndex);
            SetEyes(CurrentRecipe.eyesIndex);
            SetMouth(CurrentRecipe.mouthIndex);
            SetFacialHair(CurrentRecipe.facialHairIndex);

            if (newPalette != null)
            {
                SetHairColor(Pick(newPalette.hairColors, CurrentRecipe.hairColorIndex));
                SetSkinTone(Pick(newPalette.skinTones, CurrentRecipe.skinToneIndex));
                SetOutfitColor(Pick(newPalette.outfitColors, CurrentRecipe.outfitColorIndex));
            }

            SetEyeColor(CurrentRecipe.eyeColorIndex);

            // Eyes and mouth are never tinted in this kit (see the class
            // summary) and always stay white. The NOSE follows the skin
            // tone instead: its artwork is skin shading, so leaving it
            // white made it look like a light patch on the darker skins.
            if (eyesRenderer != null) eyesRenderer.color = Color.white;
            if (mouthRenderer != null) mouthRenderer.color = Color.white;

            FixSortingOrders();
        }

        /// <summary>Changes the hairstyle (back + front layers). With an
        /// elderly recipe the grey v11 layers are used instead of the young
        /// ones; a missing elderly sprite falls back to the young layer.
        /// </summary>
        public void SetHair(int index)
        {
            if (CurrentData == null || CurrentData.hairs == null)
                return;
            if (CurrentData.hairs.Length == 0)
            {
                if (hairBackRenderer != null) hairBackRenderer.sprite = null;
                if (hairFrontRenderer != null) hairFrontRenderer.sprite = null;
                return;
            }
            index = Mathf.Clamp(index, 0, CurrentData.hairs.Length - 1);
            if (CurrentRecipe != null)
                CurrentRecipe.hairIndex = index;
            HairStyle hair = CurrentData.hairs[index];
            bool elderly = CurrentRecipe != null && CurrentRecipe.ageIndex == 1;
            if (hairBackRenderer != null)
                hairBackRenderer.sprite = elderly && hair.backElderlySprite != null
                    ? hair.backElderlySprite : hair.backSprite;
            if (hairFrontRenderer != null)
                hairFrontRenderer.sprite = elderly && hair.frontElderlySprite != null
                    ? hair.frontElderlySprite : hair.frontSprite;
        }

        /// <summary>The base sprite for the given age: the elderly base
        /// when age is Elderly and one is assigned, else the young base.
        /// </summary>
        static Sprite ElderlyBase(PortraitData data, int ageIndex)
        {
            if (ageIndex == 1 && data.baseElderlySprite != null)
                return data.baseElderlySprite;
            return data.baseSprite;
        }

        /// <summary>Switches the portrait's age (0 Young, 1 Elderly) and
        /// rebuilds the base and hair layers with the matching sprites
        /// and hair tint.</summary>
        public void SetAge(int index)
        {
            if (CurrentRecipe == null)
                return;
            CurrentRecipe.ageIndex = Mathf.Clamp(index, 0, 1);
            if (CurrentData != null && baseRenderer != null)
                baseRenderer.sprite = ElderlyBase(CurrentData, CurrentRecipe.ageIndex);
            SetHair(CurrentRecipe.hairIndex);
            if (CurrentPalette != null)
                SetHairColor(Pick(CurrentPalette.hairColors, CurrentRecipe.hairColorIndex));
        }

        /// <summary>Changes the outfit layer.</summary>
        public void SetOutfit(int index)
        {
            SetNamed(CurrentData != null ? CurrentData.outfits : null, index, outfitRenderer,
                v => { if (CurrentRecipe != null) CurrentRecipe.outfitIndex = v; });
        }

        /// <summary>Changes the nose layer (tinted with the skin tone).</summary>
        public void SetNose(int index)
        {
            SetNamed(CurrentData != null ? CurrentData.noses : null, index, noseRenderer,
                v => { if (CurrentRecipe != null) CurrentRecipe.noseIndex = v; });
            if (noseRenderer != null)
                noseRenderer.color = currentSkin;
        }

        /// <summary>Changes the eyes layer (never tinted). When an eye
        /// color is selected, the baked variant sprite is shown.</summary>
        public void SetEyes(int index)
        {
            SetNamed(CurrentData != null ? CurrentData.eyes : null, index, eyesRenderer,
                v => { if (CurrentRecipe != null) CurrentRecipe.eyesIndex = v; });
            RefreshEyesSprite();
        }

        /// <summary>
        /// Selects the eye color: index 0 keeps the artwork's original
        /// iris; any other index swaps the eyes layer for the baked
        /// variant whose iris was recolored to that palette color (the
        /// sclera, the pupil and the highlights are untouched). If a
        /// variant is missing, the original layer stays.
        /// </summary>
        public void SetEyeColor(int index)
        {
            if (CurrentRecipe != null)
                CurrentRecipe.eyeColorIndex = index;
            RefreshEyesSprite();
        }

        void RefreshEyesSprite()
        {
            if (CurrentData == null || eyesRenderer == null || CurrentRecipe == null)
                return;
            if (CurrentData.eyes == null || CurrentData.eyes.Length == 0)
                return;
            int eyesIndex = Mathf.Clamp(CurrentRecipe.eyesIndex, 0, CurrentData.eyes.Length - 1);
            Sprite sprite = CurrentData.eyes[eyesIndex].sprite;
            int colorIndex = CurrentRecipe.eyeColorIndex;
            if (colorIndex > 0 && CurrentPalette != null && CurrentPalette.eyeColors != null
                && colorIndex < CurrentPalette.eyeColors.Length
                && CurrentData.eyeVariants != null)
            {
                string wanted = CurrentData.eyes[eyesIndex].name + "|" +
                    CurrentPalette.eyeColors[colorIndex].name;
                foreach (NamedSprite variant in CurrentData.eyeVariants)
                {
                    if (variant.name == wanted && variant.sprite != null)
                    {
                        sprite = variant.sprite;
                        break;
                    }
                }
            }
            eyesRenderer.sprite = sprite;
            eyesRenderer.color = Color.white;
        }

        /// <summary>
        /// Changes the facial hair layer (male character only; index 0
        /// means none, 1..N selects facialHairs[index - 1]). The layer
        /// is tinted with the current hair color.
        /// </summary>
        public void SetFacialHair(int index)
        {
            if (CurrentRecipe != null)
                CurrentRecipe.facialHairIndex = index;
            if (facialHairRenderer == null)
                return;
            if (CurrentData == null || CurrentData.facialHairs == null
                || index <= 0 || index > CurrentData.facialHairs.Length)
            {
                facialHairRenderer.sprite = null;
                return;
            }
            facialHairRenderer.sprite = CurrentData.facialHairs[index - 1].sprite;
            facialHairRenderer.color = currentHairColor;
        }

        /// <summary>Changes the mouth layer (never tinted).</summary>
        public void SetMouth(int index)
        {
            SetNamed(CurrentData != null ? CurrentData.mouths : null, index, mouthRenderer,
                v => { if (CurrentRecipe != null) CurrentRecipe.mouthIndex = v; });
        }

        void SetNamed(NamedSprite[] list, int index, SpriteRenderer renderer,
            System.Action<int> storeIndex)
        {
            if (list == null || renderer == null)
                return;
            if (list.Length == 0)
            {
                renderer.sprite = null;
                return;
            }
            index = Mathf.Clamp(index, 0, list.Length - 1);
            storeIndex(index);
            renderer.sprite = list[index].sprite;
            renderer.color = Color.white;
        }

        // Last hair color applied, so the facial hair can follow it.
        Color currentHairColor = Color.white;

        /// <summary>Tints both hair layers and the facial hair (multiplicative).
        /// With an elderly recipe the hair layers stay WHITE (the grey is
        /// baked in the v11 layers, the same rule as the web creator and
        /// motor.py); only the facial hair follows the hair color, since it
        /// has no elderly version.</summary>
        public void SetHairColor(Color color)
        {
            currentHairColor = color;
            Color hair = (CurrentRecipe != null && CurrentRecipe.ageIndex == 1) ? Color.white : color;
            if (hairBackRenderer != null)
                hairBackRenderer.color = hair;
            if (hairFrontRenderer != null)
                hairFrontRenderer.color = hair;
            if (facialHairRenderer != null)
                facialHairRenderer.color = color;
        }

        // Last skin tone applied, so the nose layer can follow it.
        Color currentSkin = Color.white;

        /// <summary>
        /// Tints the base layer, that is, the skin (multiplicative), and
        /// the nose layer with it: the nose artwork is skin shading and
        /// must darken together with the face on every skin tone.
        /// </summary>
        public void SetSkinTone(Color color)
        {
            currentSkin = color;
            if (baseRenderer != null)
                baseRenderer.color = color;
            if (noseRenderer != null)
                noseRenderer.color = color;
        }

        /// <summary>Tints the outfit layer (multiplicative).</summary>
        public void SetOutfitColor(Color color)
        {
            if (outfitRenderer != null)
                outfitRenderer.color = color;
        }

        /// <summary>Forces the fixed sorting orders of the layer stack.</summary>
        public void FixSortingOrders()
        {
            if (hairBackRenderer != null) hairBackRenderer.sortingOrder = 10;
            if (baseRenderer != null) baseRenderer.sortingOrder = 20;
            if (outfitRenderer != null) outfitRenderer.sortingOrder = 30;
            if (noseRenderer != null) noseRenderer.sortingOrder = 35;
            if (eyesRenderer != null) eyesRenderer.sortingOrder = 40;
            if (mouthRenderer != null) mouthRenderer.sortingOrder = 45;
            if (facialHairRenderer != null) facialHairRenderer.sortingOrder = 47;
            if (hairFrontRenderer != null) hairFrontRenderer.sortingOrder = 50;
            if (accessoryRenderer != null) accessoryRenderer.sortingOrder = 60;
        }

        static Color Pick(NamedColor[] colors, int index)
        {
            if (colors == null || colors.Length == 0)
                return Color.white;
            index = Mathf.Clamp(index, 0, colors.Length - 1);
            return colors[index].color;
        }
    }
}
