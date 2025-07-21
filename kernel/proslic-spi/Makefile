include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk
include $(INCLUDE_DIR)/package.mk

PKG_NAME:=proslic
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0

define KernelPackage/proslic-spi
  TITLE:=ProSLIC SPI Driver
  SUBMENU:=Other modules
  FILES:= \
	$(PKG_BUILD_DIR)/proslic-spi.ko
  AUTOLOAD:=$(call AutoLoad,proslic-spi,1)
  DEPENDS:=+kmod-spi-dev +kmod-sound-soc-core
endef

define KernelPackage/proslic-spi/description
 Kernel driver for ProSLIC FXS over SPI.
endef

define Build/Compile
	$(KERNEL_MAKE) M="$(PKG_BUILD_DIR)" modules
endef

$(eval $(call KernelPackage,proslic-spi))
