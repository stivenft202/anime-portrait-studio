using System;

namespace PortraitKit
{
    /// <summary>
    /// A recipe describes one built character with plain indices: which
    /// character data, which hairstyle, outfit, eyes, nose and mouth, and
    /// which palette colors. It is a small serializable value object, so it
    /// can be stored in save games, sent over the network or kept inside a
    /// ScriptableObject of your own, and later rebuilt with
    /// <see cref="PortraitView.Apply(PortraitData, PortraitRecipe, PortraitPalette)"/>.
    /// </summary>
    [Serializable]
    public class PortraitRecipe
    {
        /// <summary>Id of the PortraitData this recipe belongs to.</summary>
        public string characterId = "";

        /// <summary>Index into PortraitData.hairs.</summary>
        public int hairIndex = 0;

        /// <summary>Index into PortraitData.outfits.</summary>
        public int outfitIndex = 0;

        /// <summary>Index into PortraitData.eyes.</summary>
        public int eyesIndex = 0;

        /// <summary>Index into PortraitData.noses.</summary>
        public int noseIndex = 0;

        /// <summary>Index into PortraitData.mouths.</summary>
        public int mouthIndex = 0;

        /// <summary>Index into PortraitPalette.hairColors.</summary>
        public int hairColorIndex = 0;

        /// <summary>Index into PortraitPalette.skinTones.</summary>
        public int skinToneIndex = 0;

        /// <summary>Index into PortraitPalette.outfitColors.</summary>
        public int outfitColorIndex = 0;

        /// <summary>
        /// Index into PortraitPalette.eyeColors. Index 0 keeps the
        /// artwork's original iris; any other index swaps the eyes layer
        /// for the baked variant recolored to that iris color.
        /// </summary>
        public int eyeColorIndex = 0;

        /// <summary>
        /// Age: 0 = Young, 1 = Elderly. An elderly look uses the character's
        /// elderly base (PortraitData.baseElderlySprite, wrinkles in skin
        /// tone) and the grey v11 hair layers (PortraitData hairs'
        /// backElderlySprite / frontElderlySprite, fully grey, baked) with
        /// NO hair tint, the same rule as the web creator and motor.py.
        /// The combo code carries it as AG1 (Young) / AG2 (Elderly) at the
        /// end, after EC (and FH on the male character).
        /// </summary>
        public int ageIndex = 0;

        /// <summary>
        /// Facial hair: 0 means none; 1..N selects
        /// PortraitData.facialHairs[index - 1]. Only the male character
        /// has facial hair in this kit.
        /// </summary>
        public int facialHairIndex = 0;

        /// <summary>
        /// Short code that identifies this exact look, for example
        /// "F H3 O2 E1 N1 M2 | HC4 ST1 OC3 AG1". Piece numbers are 1-based and
        /// match the texture file numbers (Hair3, Outfit2, Eyes1, Nose1,
        /// Mouth2); HC, ST, OC and EC are 1-based positions in the palette
        /// lists (hair colors, skin tones, outfit colors). AG is the age:
        /// AG1 Young, AG2 Elderly. The demo shows
        /// this code under every generated character and the creator
        /// shows it in its panel, so a screenshot always carries the
        /// full recipe and the exact combo can be rebuilt at once.
        /// </summary>
        public string ComboCode()
        {
            string c = string.IsNullOrEmpty(characterId)
                ? "?"
                : characterId.Substring(0, 1).ToUpperInvariant();
            string code = string.Format(
                "{0} H{1} O{2} E{3} N{4} M{5} | HC{6} ST{7} OC{8} EC{9}",
                c, hairIndex + 1, outfitIndex + 1, eyesIndex + 1,
                noseIndex + 1, mouthIndex + 1, hairColorIndex + 1,
                skinToneIndex + 1, outfitColorIndex + 1, eyeColorIndex + 1);
            if (c == "M")
                code += " FH" + facialHairIndex;
            // Age goes last, after EC (and FH on the male character), the
            // same order as the web creator and motor.py: AG1 Young, AG2 Elderly.
            code += " AG" + (ageIndex + 1);
            return code;
        }

        /// <summary>
        /// Full readable description of this look with piece and color
        /// names, for console logs: anyone reading the log can rebuild
        /// the exact same character without decoding anything.
        /// </summary>
        public string Describe(PortraitData data, PortraitPalette palette)
        {
            if (data == null)
                return ComboCode();
            string text = string.Format(
                "{0} | Hair {1} | Outfit {2} | Eyes {3} | Nose {4} | Mouth {5} " +
                "| Hair color {6} | Skin {7} | Outfit color {8} | Eye color {9} | Age {10}",
                data.displayName,
                NameOf(data.hairs, hairIndex), NameOf(data.outfits, outfitIndex),
                NameOf(data.eyes, eyesIndex), NameOf(data.noses, noseIndex),
                NameOf(data.mouths, mouthIndex),
                palette != null ? NameOf(palette.hairColors, hairColorIndex) : "?",
                palette != null ? NameOf(palette.skinTones, skinToneIndex) : "?",
                palette != null ? NameOf(palette.outfitColors, outfitColorIndex) : "?",
                palette != null ? NameOf(palette.eyeColors, eyeColorIndex) : "?",
                ageIndex == 1 ? "Elderly" : "Young");
            if (data.facialHairs != null && data.facialHairs.Length > 0)
                text += " | Facial hair " + (facialHairIndex <= 0
                    ? "None" : NameOf(data.facialHairs, facialHairIndex - 1));
            return text;
        }

        static string NameOf(HairStyle[] list, int index)
        {
            if (list == null || list.Length == 0)
                return "-";
            return list[Math.Min(Math.Max(index, 0), list.Length - 1)].name;
        }

        static string NameOf(NamedSprite[] list, int index)
        {
            if (list == null || list.Length == 0)
                return "-";
            return list[Math.Min(Math.Max(index, 0), list.Length - 1)].name;
        }

        static string NameOf(NamedColor[] list, int index)
        {
            if (list == null || list.Length == 0)
                return "-";
            return list[Math.Min(Math.Max(index, 0), list.Length - 1)].name;
        }

        /// <summary>Returns an independent copy of this recipe.</summary>
        public PortraitRecipe Clone()
        {
            return new PortraitRecipe
            {
                characterId = characterId,
                hairIndex = hairIndex,
                outfitIndex = outfitIndex,
                eyesIndex = eyesIndex,
                noseIndex = noseIndex,
                mouthIndex = mouthIndex,
                hairColorIndex = hairColorIndex,
                skinToneIndex = skinToneIndex,
                outfitColorIndex = outfitColorIndex,
                eyeColorIndex = eyeColorIndex,
                facialHairIndex = facialHairIndex,
                ageIndex = ageIndex,
            };
        }
    }
}
