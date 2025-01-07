<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" 
    xmlns:t="http://www.tei-c.org/ns/1.0" 
    exclude-result-prefixes="t xs"
    version="2.0">
    <xsl:output method="xml" encoding="utf-8" indent="yes" />
    <xsl:template match="/">
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
                <xsl:copy-of select="//t:teiHeader"/>
            <text>
                <body>
                    <xsl:copy-of select="//t:div[@type='frontmatter']"/>
                    <div type="dictionary" xmlns="http://www.tei-c.org/ns/1.0">
                        <xsl:apply-templates select="//t:body/t:div[@type='dictionary']"/>
                    </div>
                </body>
            </text>
        </TEI>
    </xsl:template>
    
    <!-- 
    distinct-values(//@*/name()) - What types of attributes are there?
    distinct-values(//@*) - What attribute values are in my document?
    distinct-values(//@rend) - What values does @rend take?
    distinct-values(//name()) - What elements are there?
    -->
    
    <!-- TODO check if it worked with fixing the form@type: //entry[not(@n)]  -->
    

    <xsl:template match="t:entry">
        <entry xmlns="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">
                <xsl:choose>
                    <xsl:when test="descendant::t:form[@type = 'lemma']">
                        <xsl:value-of
                            select="substring(normalize-space(descendant::t:form[@type = 'lemma'][1]), 1, 1)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="substring(normalize-space(descendant::*[text()!=''][1]), 1,1)"/>
                        <!-- some entries have no form, resulting in empty types,
                             this simply picks up any descendant's first letter -->
                        <!-- then removing special characters, mostly resulting from different whitespaces,
                             see: https://www.oreilly.com/library/view/xslt-cookbook/0596003722/ch01s03.html -->
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            
            <xsl:attribute name="n">
                <!-- making this @n, not id, so it's not a problem if entries are double (which some are)  -->
                <xsl:choose>
                    <xsl:when test="descendant::t:form[@type = 'lemma']">
                        <xsl:value-of
                            select="concat('Ruland1612-', replace(normalize-space(descendant::t:form[@type = 'lemma'][1]), ' ', '-'))"/>
                    </xsl:when>
                    <!-- since //entry[ends-with(@n,'Ruland1612-')] yields nothing,
                    I'm assuming this covers all.. 
                    but I still needs to remove punctuation-->
                    <xsl:otherwise>
                        <xsl:value-of
                            select="concat('Ruland1612-', replace(normalize-space(descendant::*[text()!=''][1]), ' ', '-'))"/>
                    </xsl:otherwise>
                </xsl:choose>
                
                <!-- descendant::form[@type='lemma'] -->
                <!-- <xsl:value-of select="descendant::t:form[@type='lemma']"/>  -->
                <!-- replace(//t:form[@type='lemma'][1], ' ', '') -->
            </xsl:attribute>
            
            <xsl:copy-of copy-namespaces="no" select="* | @* | text() | processing-instruction() | comment()"/>
            
        </entry>
    </xsl:template>
    
    <xsl:template match="t:dictScrap">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="t:fw">
        <xsl:copy-of select="current()"/>
    </xsl:template>
    
    <xsl:template match="t:pb">
        <xsl:copy-of select="current()"/>
    </xsl:template>

</xsl:stylesheet>
