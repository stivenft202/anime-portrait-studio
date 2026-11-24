using System;
using UnityEngine;

namespace PortraitKit
{
    /// <summary>
    /// One hairstyle of a character: a back layer (drawn behind the body)
    /// and a front layer (bangs and front strands, drawn over the face).
    /// Both layers share the same 1200x1600 canvas, so they always align.
    /// </summary>
    [Serializable]
    public struct HairStyle
    {
        public string name;
        public Sprite backSprite;
        public Sprite frontSprite;

        // Elderly versions of the same hairstyle (grey v11 layers, fully
        // grey, baked): used instead of backSprite / frontSprite when the
        // recipe's age is Elderly. Leave empty to fall back to the young
        // layers. See unity/EDAD_TEXTURAS.md for the file mapping.
        public Sprite backElderlySprite;
        public Sprite frontElderlySprite;
    }

    /// <summary>
    /// A single named layer sprite (used for outfits, eyes, noses and mouths).
    /// </summary>
    [Serializable]
    public struct NamedSprite
    {
        public string name;
        public Sprite sprite;
    }

    /// <summary>
    /// All the artwork of one character: one base (body and skin), a list of
    /// hairstyles, outfits, and SEPARATE lists for the face features: eyes
    /// (eyes + brows), noses and mouths. Because the features are separate
    /// layers, any eyes can combine with any nose and any mouth.
    /// Create assets from the Unity menu:
    /// Assets &gt; Create &gt; Portrait Kit &gt; Portrait Character,
    /// or run "Tools &gt; Portrait Kit &gt; Create Data and Demo Scene" to get
    /// the two included characters (Female and Male) already wired.
    /// A <see cref="PortraitView"/> reads this data and stacks the layers.
    /// </summary>
    [CreateAssetMenu(fileName = "NewPortrait", menuName = "Portrait Kit/Portrait Character", order = 0)]
    public class PortraitData : ScriptableObject
    {
        [Header("Identity")]
        public string characterId = "character";
        public string displayName = "Character";

        [Header("Base (body and skin, one per character)")]
        public Sprite baseSprite;

        [Header("Elderly base (same character with age wrinkles, skin tone)")]
        public Sprite baseElderlySprite;

        [Header("Hairstyles (back + front layer)")]
        public HairStyle[] hairs = new HairStyle[0];

        [Header("Outfits (torso layer)")]
        public NamedSprite[] outfits = new NamedSprite[0];

        [Header("Eyes (eyes + brows in one layer)")]
        public NamedSprite[] eyes = new NamedSprite[0];

        [Header("Noses")]
        public NamedSprite[] noses = new NamedSprite[0];

        [Header("Mouths")]
        public NamedSprite[] mouths = new NamedSprite[0];

        [Header("Facial hair (male character only; empty for the female)")]
        public NamedSprite[] facialHairs = new NamedSprite[0];

        [Header("Eye color variants (baked layers named \"Eyes|Color\")")]
        public NamedSprite[] eyeVariants = new NamedSprite[0];
    }
}
