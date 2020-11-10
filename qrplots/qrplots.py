
import copy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import qrcode


class QRPlots:
    C_BACK = 0
    C_FRONT = 1
    C_FIX_BACK = 2
    C_FIX_FRONT = 3
    C_MASK = 4

    PLT_COLORS = ('white', 'black', '#bdc3c7', '#2c3e50', '#4cd137', 'magenta', 'yellow')

    MASKS = {0: lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
             1: lambda i, j: (i // 2 + j // 3) % 2 == 0,
             2: lambda i, j: ((i * j) % 3 + i + j) % 2 == 0,
             3: lambda i, j: ((i * j) % 3 + i * j) % 2 == 0,
             4: lambda i, j: i % 2 == 0,
             5: lambda i, j: (i + j) % 2 == 0,
             6: lambda i, j: (i + j) % 3 == 0,
             7: lambda i, j: j % 3 == 0}

    def __init__(self, qr_text, error_correction=qrcode.constants.ERROR_CORRECT_L):
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction,
            box_size=10,
            border=0,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        qr_data = qr.get_matrix()
        self.data = []
        for row in qr_data:
            self.data.append([QRPlots.C_FRONT if val else QRPlots.C_BACK for val in row])

        self.data_rev = self._reverse_mask()
        self.text = qr_text

        assert self.codification_mode() == 4, "Only codification mode 4 is supported (byte encoding). \
                                               Please, provide only ascii text."

    """
    It colors the fixed QR pixels. These pixels are normally used as reference to read the code.
    
    :param data: matrix containing QR data
    :returns: resulting QR matrix.
    """
    def _color_fixed_pixels(self, data=None):
        data = copy.deepcopy(self.data) if data is None else copy.deepcopy(data)

        for i in range(8):
            data[i][:8] = [QRPlots.C_FIX_FRONT
                           if val == QRPlots.C_FRONT
                           else QRPlots.C_FIX_BACK
                           for val in data[i][:8]]

            data[i][-8:] = [QRPlots.C_FIX_FRONT
                            if val == QRPlots.C_FRONT
                            else QRPlots.C_FIX_BACK
                            for val in data[i][-8:]]

            data[-8 + i][:8] = [QRPlots.C_FIX_FRONT
                                if val == QRPlots.C_FRONT
                                else QRPlots.C_FIX_BACK
                                for val in data[-8 + i][:8]]

        data[6][8:-8] = [QRPlots.C_FIX_FRONT
                         if val == QRPlots.C_FRONT
                         else QRPlots.C_FIX_BACK
                         for val in data[6][8:-8]]

        for i in range(8, len(data) - 8):
            data[i][6] = QRPlots.C_FIX_FRONT \
                if data[i][6] == QRPlots.C_FRONT \
                else QRPlots.C_FIX_BACK

        data[-8][8] = QRPlots.C_FIX_FRONT
        return data

    """
    It colors the fixed and configuration pixels.
    
    :param data: matrix containing QR data.
    :param hide_rb: to hide also the length and encoding mode pixels.
    :returns: resulting QR matrix.
    """
    def _color_cfg_pixels(self, data=None, hide_rb=False):
        data = copy.deepcopy(self.data) if data is None else copy.deepcopy(data)

        for i in range(9):
            data[i][:9] = [QRPlots.C_FIX_BACK] * 9
            data[i][-8:] = [QRPlots.C_FIX_BACK] * 8
            if i < 8:
                data[-8 + i][:8] = [QRPlots.C_FIX_BACK] * 8

        data[6][8:-8] = [QRPlots.C_FIX_BACK] * (len(data) - 16)

        for i in range(9, len(data) - 8):
            data[i][6] = QRPlots.C_FIX_BACK

        for i in range(8):
            data[-8 + i][8] = QRPlots.C_FIX_BACK

        if hide_rb:
            for i in range(6):
                data[-6 + i][-2:] = [QRPlots.C_FIX_BACK] * 2

        return data

    """
    It colors the mask over the QR data.

    :param data: matrix containing QR data.
    :param show_data: to keep the data in the bits that does not cover the mask.
    :param mask_id: ID of the mask. If no ID is selected, the on in the configuration pixels is selected.
    :returns: resulting QR matrix.
    """
    def _color_mask(self, show_data=False, mask_id=None):
        if mask_id is None:
            mask_id = self.mask_id()
        data = self._color_cfg_pixels()
        mask_fun = QRPlots.MASKS[mask_id]

        for i in range(len(data)):
            for j in range(len(data[0])):
                if data[i][j] == QRPlots.C_FIX_BACK:
                    continue

                if mask_fun(i, j):
                    data[i][j] = QRPlots.C_MASK
                elif not show_data:
                    data[i][j] = QRPlots.C_BACK

        return data

    """
    Generate a QR matrix where the data covered in the mask is inverted.

    :param data: matrix containing QR data.
    :param mask_id: ID of the mask. If no ID is selected, the on in the configuration pixels is selected.
    :returns: resulting QR matrix.
    """
    def _reverse_mask(self, mask_id=None):
        if mask_id is None:
            mask_id = self.mask_id()
        data = copy.deepcopy(self.data)
        mask = self._color_mask(mask_id=mask_id)

        for i in range(len(mask)):
            for j in range(len(mask[0])):
                if mask[i][j] == QRPlots.C_MASK:
                    data[i][j] = QRPlots.C_BACK if data[i][j] == QRPlots.C_FRONT else QRPlots.C_FRONT

        return data

    """
    :returns: Mask ID contained in the configuration pixels. 
    """
    def mask_id(self):
        return int("".join(('1' if val == QRPlots.C_FRONT else '0' for val in self.data[8][2:5])), 2)

    """
    :returns: Length of the message contained in the QR.
    """
    def msg_len(self):
        len_bin = ""
        for i in range(4):
            len_bin += "".join(map(str, self.data_rev[-6+i][-2:]))

        return int(len_bin[::-1], 2)

    """
    :returns: Codification mode.
    """
    def codification_mode(self):
        cod_mode = "".join(map(str, self.data_rev[-2][-2:]))
        cod_mode += "".join(map(str, self.data_rev[-1][-2:]))

        return int(cod_mode[::-1], 2)

    """
    Shows the original QR code.

    :param size: size in inches of the resulting image.
    """
    def plot(self, size=8):
        cmap = matplotlib.colors.ListedColormap(QRPlots.PLT_COLORS[:2], name='colors', N=None)

        fig, ax = plt.subplots(figsize=(size, size))
        ax.matshow(self.data, cmap=cmap)
        plt.show()

    """
    Shows the original QR code, coloring the fixed pixels and pointing out with rectangles the different configuration pixels.

    :param size: size in inches of the resulting image.
    :param linewidth: width of the rectangles lines.
    :param off: parameter to adjust the lines to avoid rectangles overlapping.
    :param off2: parameter to adjust the lines to avoid rectangles overlapping.
    """
    def plot_cfg_info(self, size=8, linewidth=3, off=0.5, off2=0.1):
        data = self._color_fixed_pixels()
        cmap = matplotlib.colors.ListedColormap(QRPlots.PLT_COLORS[:4], name='colors', N=None)

        fig, ax = plt.subplots(figsize=(size, size))
        ax.matshow(data, cmap=cmap)

        # Error correction level
        ax.add_patch(patches.Rectangle((0 - off + off2, 8 - off), 2 - off2, 1, linewidth=linewidth, edgecolor='r',
                                       facecolor='none'))
        ax.add_patch(
            patches.Rectangle((8 - off, len(data) - 2 - off + off2), 1, 2 - off2, linewidth=linewidth, edgecolor='r',
                              facecolor='none'))

        # Mask pattern
        ax.add_patch(patches.Rectangle((2 - off + off2, 8 - off), 3 - off2, 1, linewidth=linewidth, edgecolor='g',
                                       facecolor='none'))
        ax.add_patch(
            patches.Rectangle((8 - off, len(data) - 5 - off + off2), 1, 3 - off2, linewidth=linewidth, edgecolor='g',
                              facecolor='none'))

        # Format error correction
        ax.add_patch(patches.Rectangle((5 - off + off2, 8 - off), 1 - off2, 1, linewidth=linewidth, edgecolor='#e056fd',
                                       facecolor='none'))
        ax.add_patch(
            patches.Rectangle((7 - off, 8 - off), 1, 1, linewidth=linewidth, edgecolor='#e056fd', facecolor='none'))
        ax.add_patch(patches.Rectangle((8 - off, len(data) - 7 - off), 1, 2, linewidth=linewidth, edgecolor='#e056fd',
                                       facecolor='none'))
        ax.add_patch(
            patches.Rectangle((8 - off, 0 - off + off2), 1 - off2, 6 - off2, linewidth=linewidth, edgecolor='#e056fd',
                              facecolor='none'))
        ax.add_patch(
            patches.Rectangle((8 - off, 7 - off + off2), 1 - off2, 2 - off2, linewidth=linewidth, edgecolor='#e056fd',
                              facecolor='none'))
        ax.add_patch(
            patches.Rectangle((len(data) - 8 - off, 8 - off), 8 - off2, 1, linewidth=linewidth, edgecolor='#e056fd',
                              facecolor='none'))

        # Encoding mode
        ax.add_patch(
            patches.Rectangle((len(data) - 2 - off, len(data) - 2 - off), 2 - off2, 2 - off2, linewidth=linewidth,
                              edgecolor='#7ed6df', facecolor='none'))

        # Message length
        ax.add_patch(
            patches.Rectangle((len(data) - 2 - off, len(data) - 6 - off), 2 - off2, 4 - off2, linewidth=linewidth,
                              edgecolor='#f0932b', facecolor='none'))

        plt.show()

    """
    Shows the original QR code, coloring the fixed pixels.

    :param size: size in inches of the resulting image.
    """
    def plot_fixed(self, size=8):
        data = self._color_cfg_pixels()
        cmap = matplotlib.colors.ListedColormap(QRPlots.PLT_COLORS[:3], name='colors', N=None)

        fig, ax = plt.subplots(figsize=(size, size))
        ax.matshow(data, cmap=cmap)
        plt.show()

    """
    Shows the QR code, with an specific mask colored over it.

    :param size: size in inches of the resulting image.
    """
    def plot_mask(self, size=8, show_data=False, mask_id=None):
        data = self._color_mask(show_data, mask_id)
        cmap = matplotlib.colors.ListedColormap(QRPlots.PLT_COLORS[:5], name='colors', N=None)

        fig, ax = plt.subplots(figsize=(size, size))
        ax.matshow(data, cmap=cmap)
        plt.show()

    """
    Shows the resulting QR code when the pixels covered by the mask are inverted.

    :param size: size in inches of the resulting image.
    :param grid: shows a grid over the QR code.
    """
    def plot_reversed(self, size=8, grid=True):
        cmap = matplotlib.colors.ListedColormap(QRPlots.PLT_COLORS[:3], name='colors', N=None)

        fig, ax = plt.subplots(figsize=(size, size))
        ax.matshow(self._color_cfg_pixels(self.data_rev), cmap=cmap)

        if grid:
            plt.gca().set_xticks([x - 0.5 for x in range(len(self.data_rev))], minor='true')
            plt.gca().set_yticks([y - 0.55 for y in range(len(self.data_rev))], minor='true')
            plt.grid(which='minor')

        plt.show()


if __name__ == '__main__':
    qrp = QRPlots("hey there")
    qrp.plot_reversed()
    print(qrp.codification_mode())
