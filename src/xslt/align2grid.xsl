<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	xmlns:archimate="http://www.archimatetool.com/archimate">

	<xsl:output method="xml" indent="yes"/>

	<xsl:template match="@* | node()">
		<xsl:copy>
			<xsl:apply-templates select="@* | node()"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="bounds">
		<xsl:copy><!-- skopiruj element a zatial nic viac -->
			<xsl:attribute name="x"><xsl:value-of select="round(@x div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="y"><xsl:value-of select="round(@y div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="width"><xsl:value-of select="round(@width div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="height"><xsl:value-of select="round(@height div 5) * 5"/></xsl:attribute>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="bendpoint">
		<xsl:copy><!-- skopiruj element a zatial nic viac -->
			<xsl:attribute name="startX"><xsl:value-of select="round(@startX div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="startY"><xsl:value-of select="round(@startY div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="endX"><xsl:value-of select="round(@endX div 5) * 5"/></xsl:attribute>
			<xsl:attribute name="endY"><xsl:value-of select="round(@endY div 5) * 5"/></xsl:attribute>
		</xsl:copy>
	</xsl:template>
	
</xsl:stylesheet>