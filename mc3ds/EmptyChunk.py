import anvil
from anvil.errors import OutOfBoundsCoordinates
import array
from nbt import nbt

class EmptyChunk(anvil.EmptyChunk):
    """
    A wrapper class for anvil.EmptyChunk that handles
    biome sections for chunk version 2566
    """
    def __init__(self, x, z):
        super().__init__(x, z)
        self.version = 2566
        self.biomesData = None

    def paint_biome_y_section(self, y_section, biome_id):
        """
        Paints a section in y level of the chunk with a biome id.
        Use y section position (0-63)
        
        :param y_section: The y section to paint
        :param biome_id: The biome id to paint

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If Y is not in the proper range
        """
        if y_section < 0 or y_section > 63:
            raise OutOfBoundsCoordinates(f'X ({y_section!r}) must be in range of 0 to 63')
        
        if self.biomesData is None:
            self.biomesData = array.array("l", [1] * (4*4) * 64) # 64 sections in Y
        for y4 in range(y_section * 4, y_section * 4 + 4):
            for z4 in range(4):
                for x4 in range(4):
                    index = y4 * 16 + z4 * 4 + x4
                    self.biomesData[index] = biome_id

    def paint_biome_column(self, c_x, c_z, biome_id):
        """
        Paints a column of the chunk with a biome id.
        Use x and z coordinates of the column in the chunk
        
        :param c_x: The x coordinate of the column
        :param c_z: The z coordinate of the column
        :param biome_id: The biome id to paint

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X or Z are not in the proper range
        """
        if c_x < 0 or c_x > 15:
            raise OutOfBoundsCoordinates(f'X ({c_x!r}) must be in range of 0 to 15')
        if c_z < 0 or c_z > 15:
            raise OutOfBoundsCoordinates(f'Z ({c_z!r}) must be in range of 0 to 15')
        
        if self.biomesData is None:
            self.biomesData = array.array("l", [1] * (4*4) * 64) # 64 sections in Y
        x4 = c_x // 4
        z4 = c_z // 4
        for y4 in range(64):
            index = y4 * 16 + z4 * 4 + x4
            self.biomesData[index] = biome_id

    def save(self):
        root = super().save()
        level = root.tags[-1]
        if self.biomesData != None:
            biomes = nbt.TAG_Int_Array(name="Biomes")
            biomes.value = self.biomesData
            level.tags.append(biomes)
        return root