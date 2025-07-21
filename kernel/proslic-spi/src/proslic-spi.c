// SPDX-License-Identifier: GPL-2.0-only

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/interrupt.h>
#include <linux/miscdevice.h>
#include <linux/of.h>
#include <linux/of_gpio.h>
#include <linux/poll.h>

#include <linux/spi/spi.h>
#include <sound/soc.h>
#include <sound/pcm_params.h>

#define DRIVER_NAME "proslic-spi"
#define DEVICE_NAME "proslic"

#define PROSLIC_MAX_CHANNELS 2
#define PROSLIC_RETRIES 100

/* Channel Addresses */
#define PROSLIC_CHAN_ID_0 0x00
#define PROSLIC_CHAN_ID_1 0x10
#define PROSLIC_CHAN_BCAST 0xFF

/* SPI Op Codes */
#define PROSLIC_OP_WR 0x20
#define PROSLIC_OP_RD 0x60
#define PROSLIC_OP_BCAST 0x80

/* Registers */
#define PROSLIC_REG_ID 0x00
#define PROSLIC_REG_RESET 0x01
#define PROSLIC_REG_RAMSTAT 0x04
#define PROSLIC_REG_RAM_ADDR_HI 0x05
#define PROSLIC_REG_RAM_D0 0x06
#define PROSLIC_REG_RAM_D1 0x07
#define PROSLIC_REG_RAM_D2 0x08
#define PROSLIC_REG_RAM_D3 0x09
#define PROSLIC_REG_RAM_ADDR_LO 0x0A

#define PROSLIC_REG_IRQ0 0x11

/* IOCTL Commands */
#define IOCTL_READ_REG _IOR('p', 1, struct proslic_access)
#define IOCTL_WRITE_REG _IOW('p', 2, struct proslic_access)
#define IOCTL_READ_RAM _IOR('p', 3, struct proslic_access)
#define IOCTL_WRITE_RAM _IOW('p', 4, struct proslic_access)
// #define IOCTL_LOAD_FW       _IO('p', 5)
// #define IOCTL_GET_MODEL     _IOR('p', 6, struct proslic_access)
#define IOCTL_RESET_DEVICE _IOW('p', 7, struct proslic_access)

struct proslic_access
{
    __u8 channel;
    __u16 address;
    __u32 data;
};

struct proslic_device
{
    struct spi_device *spi;
    struct miscdevice mdev;
    struct gpio_desc *reset_gpio;

    int num_channels;

    /* IRQ */
    bool irq_enabled;
    wait_queue_head_t irq_wq;
    atomic_t irq_flag;
};

static const int channel_addrs[PROSLIC_MAX_CHANNELS] = {
    0x00, 0x10 //, 0x08, 0x14
};

static int proslic_reset(struct proslic_device *dev)
{
    if (!dev->reset_gpio)
        return -ENODEV;

    gpiod_set_value(dev->reset_gpio, 1);
    mdelay(25);
    gpiod_set_value(dev->reset_gpio, 0);
    mdelay(10);

    return 0;
}

static int proslic_read_reg(struct spi_device *spi, u8 chan, u8 reg, u8 *value)
{
    struct spi_message msg;
    struct spi_transfer tctrl = {
        .tx_buf = buffer,
        .len = 2,
        .cs_change = 1,
    };
    struct spi_transfer tval = {
        .rx_buf = &buffer[2],
        .len = 2,
        .cs_change = 0,
    };
    uint8_t buffer[4];
    int ret;

    if (!spi)
        return -ENODEV;

    if (chan >= PROSLIC_MAX_CHANNELS)
    {
        dev_err(&spi->dev, "Failed to read register: %02X, invalid channel %u\n",
                reg, chan);
        return -EFAULT;
    }

    /* First byte contains opcode and channel address */
    buffer[0] = PROSLIC_OP_RD | channel_addrs[chan];
    /* Second byte is the register to read */
    buffer[1] = reg;
    /* Third byte is the register value */
    buffer[3] = 0xFF;
    *value = 0xFF;

    spi_message_init(&msg);
    spi_message_add_tail(&tctrl, &msg);
    spi_message_add_tail(&tval, &msg);

    ret = spi_sync(spi, &msg);
    if (ret)
    {
        dev_err(&spi->dev, "Failed to read register! chan = %u(0x%02X) reg = 0x%02X \n",
                chan, channel_addrs[chan], reg);
        return ret;
    }

    dev_dbg(&spi->dev, "ReadREG - chan = %u reg = %u data = 0x%02X\n",
            chan, reg, *value);

    /* copy the read value*/
    *value = buffer[2];

    return 0;
}

static int proslic_write_reg(struct spi_device *spi, u8 chan, u8 reg, u8 value)
{
    uint8_t buffer[4];
    struct spi_message msg;
    struct spi_transfer tctrl = {
        .tx_buf = buffer,
        .len = 2,
        .cs_change = 1,
    };
    struct spi_transfer tval = {
        .tx_buf = &buffer[2],
        .len = 2,
        .cs_change = 0,
    };
    int ret;

    if (!spi)
        return -ENODEV;

    if (chan >= PROSLIC_MAX_CHANNELS && chan != PROSLIC_CHAN_BCAST)
    {
        dev_err(&spi->dev, "Failed to write register: %02X, invalid channel %u\n",
                reg, chan);
        return -EFAULT;
    }

    /* First byte contains opcode and channel address */
    if (chan == PROSLIC_CHAN_BCAST)
    {
        buffer[0] = PROSLIC_OP_WR | PROSLIC_OP_BCAST;
    }
    else
    {
        buffer[0] = PROSLIC_OP_WR | channel_addrs[chan];
    }
    /* Second byte is the register to write */
    buffer[1] = reg;
    /* 3rd and 4th byte are the register value */
    buffer[2] = value;
    buffer[3] = value;

    spi_message_init(&msg);
    spi_message_add_tail(&tctrl, &msg);
    spi_message_add_tail(&tval, &msg);

    ret = spi_sync(spi, &msg);
    if (ret)
    {
        dev_err(&spi->dev, "Failed to write register! chan = %u(0x%02X) reg = 0x%02X value = 0x%02X\n",
                chan, channel_addrs[chan], reg, value);
        return ret;
    }

    dev_dbg(&spi->dev, "WriteREG - chan = %u reg = %u data = 0x%02X\n",
            chan, reg, value);

    return 0;
}

static int proslic_wait_ram(struct proslic_device *dev, u8 channel)
{
    int count = PROSLIC_RETRIES;
    u8 data = 0xFF;

    while (count-- > 0 && (data & 0x1))
    {
        if (proslic_read_reg(dev->spi, channel, PROSLIC_REG_RAMSTAT, &data))
            return -EIO;
        if (data & 0x1)
            mdelay(5);
    }

    return (count <= 0) ? -ETIMEDOUT : 0;
}

static int proslic_write_ram(struct proslic_device *dev, u8 channel, u16 addr, u32 data)
{
    int ret;

    // Wait for the RAM to be available or no operation is in progress
    ret = proslic_wait_ram(dev, channel);
    if (ret)
        return ret;

    // The data is 29bit so we have to split
    // into different registers to write it.
    //
    // The address seems to be 11/12bit so we have to split the
    // address in two. We don't know why we need to write the HI part
    // in the beginning and the LOW part at the end.
    // Probably they will internally signal an BEGIN and COMMIT operaion
    // The LOW part of the address is varing and we think that only the
    // top 4 bits are spllitted.
    //
    // The biggest Hi address observed is 0xC0.
    // We have observed that the lowest 5 bits are always 0

    // The HI part of the address is created by taking
    // the most 3/4 significant bits and by shifting them right by 3.
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_ADDR_HI, (addr >> 3) & 0xE0);

    // In the ram values set on data rgisters always have the last
    // 3-bits set to 0 so I'm assuming the data is shifted
    // to keep a sort of 32bit MSB alignement. This remembers
    // left justified PCM / I2S.
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_D0, (data << 3) & 0xFF);
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_D1, (data >> 5) & 0xFF);
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_D2, (data >> 13) & 0xFF);
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_D3, (data >> 21) & 0xFF);

    // Write/COMMIT OPs?
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_ADDR_LO, addr & 0xFF);

    // Write operation succeeded?
    return proslic_wait_ram(dev, channel);
}

static int proslic_read_ram(struct proslic_device *dev, u8 channel, u16 addr, u32 *data)
{
    int ret;
    u8 d0, d1, d2, d3;

    // Wait for the RAM to be available or no operation is in progress
    ret = proslic_wait_ram(dev, channel);
    if (ret)
        return ret;

    // HI RAM ADDR
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_ADDR_HI, (addr >> 3) & 0xE0);

    // LOW RAM ADDR
    proslic_write_reg(dev->spi, channel, PROSLIC_REG_RAM_ADDR_LO, addr & 0xFF);

    // Wait for the RAM to be available or no operation is in progress
    ret = proslic_wait_ram(dev, channel);
    if (ret)
        return ret;

    // READ DATA Registers
    proslic_read_reg(dev->spi, channel, PROSLIC_REG_RAM_D0, &d0);
    proslic_read_reg(dev->spi, channel, PROSLIC_REG_RAM_D1, &d1);
    proslic_read_reg(dev->spi, channel, PROSLIC_REG_RAM_D2, &d2);
    proslic_read_reg(dev->spi, channel, PROSLIC_REG_RAM_D3, &d3);

    *data = ((u32)d3 << 21) | ((u32)d2 << 13) | ((u32)d1 << 5) | ((u32)d0 >> 3);
    return 0;
}

static int proslic_chip_info(struct proslic_device *dev, u8 channel, u8 *id)
{
    return proslic_read_reg(dev->spi, channel, PROSLIC_REG_ID, id);
}

static int proslic_probe_channels(struct proslic_device *dev)
{
    struct spi_device *spi = dev->spi;
    int ret;
    u8 i, id;

    for (i = 0; i < PROSLIC_MAX_CHANNELS; i++)
    {
        dev_info(&spi->dev, "ProSLIC - Probing chan = %u\n", i);

        ret = proslic_chip_info(dev, i, &id);
        if (ret)
        {
            dev_err(&spi->dev, "Failed to probe.\n");
            return ret;
        }

        if (id == 0xFF)
        {
            dev_warn(&spi->dev, "Channel not found! channel = %u\n", i);
            continue;
        }
        dev_info(&spi->dev, "ProSLIC - Found channel=%d chip-id=0x%02X\n", i, id);

        // dev->channels[i].chip_id = id;
        // dev->channels[i].channel_id = i;
        dev->num_channels++;
    }

    return 0;
}

/* IRQ Handler */
static irqreturn_t proslic_irq_handler(int irq, void *data)
{
    struct proslic_device *proslic = data;

    atomic_set(&proslic->irq_flag, 1);
    wake_up_interruptible(&proslic->irq_wq);

    return IRQ_HANDLED;
}

/* Blocking read() for IRQ */
static ssize_t proslic_char_read(struct file *file, char __user *buf, size_t count, loff_t *ppos)
{
    struct proslic_device *proslic = file->private_data;
    struct spi_device *spi = proslic->spi;
    uint8_t val;
    int ret;

    if (!proslic->irq_enabled)
        return -ENODEV;

    ret = wait_event_interruptible(proslic->irq_wq, atomic_read(&proslic->irq_flag));
    if (ret)
        return ret;

    atomic_set(&proslic->irq_flag, 0);

    /* Read register IRQ0 */
    ret = proslic_read_reg(proslic->spi, 0, PROSLIC_REG_IRQ0, &val);
    if (ret)
    {
        dev_err(&spi->dev, "Failed to read IRQ0 status reg: %d\n", ret);
        return ret;
    }

    if (count < sizeof(val))
        return -EINVAL;

    if (copy_to_user(buf, &val, sizeof(val)))
        return -EFAULT;

    return sizeof(val);
}

/* poll() support */
static __poll_t proslic_char_poll(struct file *file, poll_table *wait)
{
    struct proslic_device *proslic = file->private_data;

    if (!proslic->irq_enabled)
        return 0;

    poll_wait(file, &proslic->irq_wq, wait);

    if (atomic_read(&proslic->irq_flag))
        return POLLIN | POLLRDNORM;

    return 0;
}

static long proslic_char_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct proslic_device *proslic = file->private_data;
    struct proslic_access acc;
    u8 val;
    int ret = 0;

    if (copy_from_user(&acc, (void __user *)arg, sizeof(acc)))
        return -EFAULT;

    switch (cmd)
    {
    case IOCTL_READ_REG:
        ret = proslic_read_reg(proslic->spi, acc.channel, acc.address, &val);
        acc.data = val;
        if (!ret && copy_to_user((void __user *)arg, &acc, sizeof(acc)))
            return -EFAULT;
        break;

    case IOCTL_WRITE_REG:
        ret = proslic_write_reg(proslic->spi, acc.channel, acc.address, acc.data);
        break;

    case IOCTL_READ_RAM:
        ret = proslic_read_ram(proslic, acc.channel, acc.address, &acc.data);
        if (!ret && copy_to_user((void __user *)arg, &acc, sizeof(acc)))
            return -EFAULT;
        break;

    case IOCTL_WRITE_RAM:
        ret = proslic_write_ram(proslic, acc.channel, acc.address, acc.data);
        break;

    case IOCTL_RESET_DEVICE:
        ret = proslic_reset(proslic);
        break;

    default:
        ret = -ENOTTY;
    }

    return ret;
}

static int proslic_char_open(struct inode *inode, struct file *file)
{
    struct miscdevice *mdev = file->private_data;
    struct proslic_device *proslic = dev_get_drvdata(mdev->parent);

    file->private_data = proslic;
    return 0;
}

static const struct file_operations proslic_char_fops = {
    .owner = THIS_MODULE,
    .open = proslic_char_open,
    .read = proslic_char_read,
    .poll = proslic_char_poll,
    .unlocked_ioctl = proslic_char_ioctl,
};

static int proslic_codec_probe(struct snd_soc_component *component)
{
    dev_info(component->dev, "%s\n", __func__);
    return 0;
}

static void proslic_codec_remove(struct snd_soc_component *component)
{
    dev_info(component->dev, "%s\n", __func__);
}

static const struct snd_soc_dapm_widget proslic_codec_dapm_widgets[] = {
    SND_SOC_DAPM_INPUT("VINP"),
    SND_SOC_DAPM_OUTPUT("VOUTP"),
};

static const struct snd_soc_dapm_route proslic_codec_dapm_routes[] = {
    {"VOUTP", NULL, "Playback"},
    {"Capture", NULL, "VINP"},
};

static int proslic_codec_set_fmt(struct snd_soc_dai *dai, unsigned int format)
{
    struct snd_soc_component *component = dai->component;
    struct proslic_device *proslic = snd_soc_component_get_drvdata(component);

    switch (format & SND_SOC_DAIFMT_MASTER_MASK)
    {
    case SND_SOC_DAIFMT_CBC_CFC:
        break;
    default:
        return -EINVAL;
    }

    switch (format & SND_SOC_DAIFMT_INV_MASK)
    {
    case SND_SOC_DAIFMT_NB_IF:
    case SND_SOC_DAIFMT_IB_NF:
    case SND_SOC_DAIFMT_IB_IF:
        // FIXME: we should get the bit polarity and store in proslic private data
        // this might be useful for userspace driver to configure the chip
        if (proslic->irq_enabled)
        {
            // NOP
        }
        break;
    default:
        break;
    }

    switch (format & SND_SOC_DAIFMT_FORMAT_MASK)
    {
    case SND_SOC_DAIFMT_I2S:
        break;
    default:
        return -EINVAL;
    }

    return 0;
}

static int proslic_codec_hw_params(struct snd_pcm_substream *substream,
                                   struct snd_pcm_hw_params *hw_params, struct snd_soc_dai *dai)
{
    struct snd_soc_component *component = dai->component;
    struct proslic_device *proslic = snd_soc_component_get_drvdata(component);

    int word_len = params_physical_width(hw_params);
    int aud_bit = params_width(hw_params);

    dev_info(dai->dev, "format: 0x%08x\n", params_format(hw_params));
    dev_info(dai->dev, "rate: 0x%08x\n", params_rate(hw_params));
    dev_info(dai->dev, "word_len: %d, aud_bit: %d\n", word_len, aud_bit);
    if (word_len != 16)
    {
        dev_err(dai->dev, "not supported word length\n");
        return -ENOTSUPP;
    }

    // FIXME: we should pass the word_len to userspace for TDM slot calculation
    if (false)
    {
        proslic_probe_channels(proslic);
    }

    dev_info(dai->dev, "%s: --\n", __func__);
    return 0;
}

static const struct snd_soc_dai_ops proslic_codec_aif_ops = {
    .set_fmt = proslic_codec_set_fmt,
    .hw_params = proslic_codec_hw_params,
};

static struct snd_soc_dai_driver proslic_codec_dai = {
    // .name = "proslic-fxs",
    .name = "wm8960-hifi",
    .playback = {
        .stream_name = "Playback",
        .channels_min = 1,
        .channels_max = 2,
        .rates = SNDRV_PCM_RATE_16000,
        .formats = SNDRV_PCM_FMTBIT_S16_LE,
    },
    .capture = {
        .stream_name = "Capture",
        .channels_min = 1,
        .channels_max = 2,
        .rates = SNDRV_PCM_RATE_16000,
        .formats = SNDRV_PCM_FMTBIT_S16_LE,
    },
    /* dai properties */
    .symmetric_rate = 1,
    .symmetric_channels = 1,
    .symmetric_sample_bits = 1,
    /* dai operations */
    .ops = &proslic_codec_aif_ops,
};

static const struct snd_soc_component_driver proslic_codec_driver = {
    .probe = proslic_codec_probe,
    .remove = proslic_codec_remove,

    .dapm_widgets = proslic_codec_dapm_widgets,
    .num_dapm_widgets = ARRAY_SIZE(proslic_codec_dapm_widgets),
    .dapm_routes = proslic_codec_dapm_routes,
    .num_dapm_routes = ARRAY_SIZE(proslic_codec_dapm_routes),

    .idle_bias_on = false,
};

static int proslic_probe(struct spi_device *spi)
{
    struct proslic_device *proslic;
    int ret;

    proslic = kzalloc(sizeof(*proslic), GFP_KERNEL);
    if (!proslic)
        return -ENOMEM;

    spi_set_drvdata(spi, proslic);

    proslic->spi = spi;

    /* Reset line is active HIGH */
    proslic->reset_gpio = devm_gpiod_get(&spi->dev, "reset", GPIOD_OUT_LOW);
    if (IS_ERR(proslic->reset_gpio))
    {
        dev_err(&spi->dev, "Failed to get reset GPIO\n");
        ret = PTR_ERR(proslic->reset_gpio);
        goto err_free;
    }
    dev_info(&spi->dev, "reset_gpio = %d\n", desc_to_gpio(proslic->reset_gpio));

    /* Optional IRQ */
    proslic->irq_enabled = spi->irq > 0;
    if (proslic->irq_enabled)
    {
        ret = devm_request_threaded_irq(&spi->dev, spi->irq,
                                        NULL, proslic_irq_handler,
                                        IRQF_ONESHOT, DRIVER_NAME, proslic);
        if (ret)
            return ret;
        dev_info(&spi->dev, "IRQ %d registered\n", spi->irq);
    }

    /* Register Alsa Codec */
    ret = snd_soc_register_component(&spi->dev, &proslic_codec_driver,
                                     &proslic_codec_dai, 1);
    if (ret)
    {
        dev_err(&spi->dev, "Failed to snd_soc_register_component: %d\n", ret);
        return ret;
    }

    /* Register Char Device */
    proslic->mdev.minor = MISC_DYNAMIC_MINOR;
    proslic->mdev.name = DEVICE_NAME;
    proslic->mdev.fops = &proslic_char_fops;
    proslic->mdev.parent = &spi->dev;

    ret = misc_register(&proslic->mdev);
    if (ret)
    {
        dev_err(&spi->dev, "failed to register misc device\n");
        goto err_free;
    }

    dev_info(&spi->dev, "/dev/%s registered\n", DEVICE_NAME);
    dev_info(&spi->dev, "ProSLIC SPI driver loaded\n");

    return 0;

err_free:
    kfree(proslic);
    return ret;
}

static void proslic_remove(struct spi_device *spi)
{
    struct proslic_device *dev = spi_get_drvdata(spi);

    snd_soc_unregister_component(&spi->dev);
    misc_deregister(&dev->mdev);
    kfree(dev);
}

static const struct of_device_id proslic_of_match[] = {
    {.compatible = "silabs,proslic-spi"},
    {.compatible = "silabs,proslic_spi"},
    {/* sentinel */}};
MODULE_DEVICE_TABLE(of, proslic_of_match);

static struct spi_driver proslic_driver = {
    .driver = {
        .name = DRIVER_NAME,
        .of_match_table = proslic_of_match,
    },
    .probe = proslic_probe,
    .remove = proslic_remove,
};

module_spi_driver(proslic_driver);

MODULE_DESCRIPTION("ProSLIC SPI driver with UAPI");
MODULE_AUTHOR("Nicolò Veronese <nicveronese@gmail.com>");
MODULE_LICENSE("GPL");
