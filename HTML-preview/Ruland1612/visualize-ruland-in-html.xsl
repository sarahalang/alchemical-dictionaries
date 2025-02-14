<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:t="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs"
    version="2.0">
    <xsl:output method="html" encoding="utf-8" indent="yes" />

<!-- 2025-02: Brief documentation note for this XSLT file
    This contains a simple, unfinished transformation to create a basic, ugly HTML preview for the Ruland dictionary TEI-XSL.
    These dictionary files are too long to keep an overview without it. 
    A copy of this should also be adapted to the Sommerhoff dictionary later to visualize it.
    Maybe the template can be made a bit nicer to that it becomes actually usable as a mini "data viewer" website.
    -->
    
    <xsl:template match="/">
        <!-- ________________________________________________________________________________ -->
        
        <xsl:text disable-output-escaping='yes'>&lt;!DOCTYPE html&gt;
        
        </xsl:text>
        
        <html lang="en">
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"/>
                <meta name="description" content=""/>
                <meta name="author" content=""/>
                <link rel="icon" href="https://getbootstrap.com/favicon.ico"/>
                
                <title><xsl:value-of select="//t:title"/></title>
                
                <!-- Bootstrap core CSS -->
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css" integrity="sha384-GJzZqFGwb1QTTN6wy59ffF1BuGJpLSa9DkKMp0DgiMDm4iYMj70gZWKYbI706tWS" crossorigin="anonymous"/>
                
                <!-- Bootstrap core JavaScript
    ================================================== -->
                <!-- place at the end of the document so the pages load faster -->
                <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js" integrity="sha384-wHAiFfRlMFy6i5SRaxvfOCifBUQy1xHdJ/yoi7FRNXMRBu5WHdZYu1hA6ZOblgut" crossorigin="anonymous"></script>
                <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js" integrity="sha384-B0UglyR+jN6CkvvICOB2joaf5I4l3gm9GU6Hc1og6Ls7i6U/mkkaduKaBhlAXv9k" crossorigin="anonymous"></script>
                
                <!-- Javascript Toggle -->
                <!-- Roman Bleier's Simple Checkbox Menu (GAMS Wippet) -->
                <script>
                    /*alert('This is a test');*/
                    (function ( $ ) {
                    /*simpleCheckboxMenu (SCM): JQUery Plugin for simple Dom visualisation via toggling a class
                    The Plugin attaches a click event (may be changed to any other event).
                    On the checkbox input element the class 'scm-checkbox' is required
                    Also required are two additional attributes on the checkbox:
                    "data-scm-target": contains a Jqery selector string to the elements on which the class should be toggled
                    "data-scm-class": contains the class name that should be toggled on the above elements*/
                    
                    $(document).ready(function(){
                    
                    function triggerEvent($ele){
                    var target = $($ele).attr("data-scm-target");
                    var classToToggle = $($ele).attr("data-scm-class");
                    //console.log("Target Jquery selector is: "+target);
                    //console.log("Class to toggle is: "+classToToggle);
                    $(target).toggleClass(classToToggle);
                    }
                    
                    
                    $("input.scm-checkbox").on("click", function(){
                    //console.log("click event works");
                    triggerEvent(this);
                    });	
                    
                    $("input.scm-checkbox:checked").each(function(){
                    //console.log("checkbox checked event works");
                    triggerEvent(this);
                    });
                    });
                    }(jQuery));
                </script>
                
                <!-- Tooltip -->
                <script>
                    $(document).ready(function(){
                    $('[data-toggle="tooltip"]').tooltip();   
                    });
                </script>
                <!-- Custom inline CSS styles for this template -->
                <style>
                    body {
                    padding-top: 5rem;
                    }
                    .starter-template {
                    padding: 3rem 1.5rem;
                    text-align: center;
                    }
                    .scm-person{
                    background-color:DarkSalmon;
                    }
                    .person, .place {
                    font-style: italic;
                    }
                </style>
                
            </head>
            
            <body>
                
                <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
                    <a class="navbar-brand" href="#">Navbar</a>
                    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarsExampleDefault" aria-controls="navbarsExampleDefault" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    
                    <div class="collapse navbar-collapse" id="navbarsExampleDefault">
                        <ul class="navbar-nav mr-auto">
                            <li class="nav-item active">
                                <a class="nav-link" href="#">Home <span class="sr-only">(current)</span></a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="#">Link</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link disabled" href="#">Disabled</a>
                            </li>
                            <li class="nav-item dropdown">
                                <a class="nav-link dropdown-toggle" href="http://example.com" id="dropdown01" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</a>
                                <div class="dropdown-menu" aria-labelledby="dropdown01">
                                    <a class="dropdown-item" href="#">Action</a>
                                    <a class="dropdown-item" href="#">Another action</a>
                                    <a class="dropdown-item" href="#">Something else here</a>
                                </div>
                            </li>
                        </ul>
                        <form class="form-inline my-2 my-lg-0">
                            <input class="form-control mr-sm-2" type="text" placeholder="Search" aria-label="Search" />
                            <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
                        </form>
                    </div>
                </nav>
                
                <!-- ________________________________________________________________________________ -->
                
                <main role="main" class="container">
                    
                    <div class="starter-template">
                        <h1>Bootstrap starter template: <xsl:value-of select="//t:title"/></h1>
                        <p class="lead">Use this document as a way to quickly start any new project.<br/> 
                            TODO list entires</p>
                    </div>
                    <div>
                        <ul class="checkbox">
                            <li><input class="scm-checkbox" data-scm-target=".person" data-scm-class="scm-person" type="checkbox"> 
                            </input><label><xsl:text>Show persons (dummy because no persons annotated in TEI)</xsl:text></label></li>
                        </ul>
                    </div>
                    <!-- ________________________________________________________________________________ -->
                    
                    <div>
                            <ul>
                                <xsl:for-each select="//t:milestone">
                                    <li>
                                        <a class="alphabetical-index" href="#{@n}">
                                            <!-- TODO create linking: this does not yet do anything -->
                                            <xsl:value-of select="@n"/>
                                        </a>
                                    </li>
                                </xsl:for-each>
                        </ul>
                    </div>
                    <!-- ________________________________________________________________________________ -->
                    
                    <div>
                        <p>TODO create some sort of header for the TEIheader metadata</p>
                    </div>
                    <!-- ________________________________________________________________________________ -->
                    
                    <div>
                        <xsl:apply-templates/>
                    </div>
                    
                </main><!-- /.container -->
                
            </body>
        </html>
        
    </xsl:template>
    
    
    <xsl:template match="t:div">
        <div>
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    
    <xsl:template match="t:entry">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>    
    
    <xsl:template match="t:p">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    
    <xsl:template match="t:form">
        <b>
            <xsl:apply-templates/>
        </b>
    </xsl:template>
    
    <xsl:template match="t:cit">
        <i>
            <xsl:apply-templates/>
        </i>
    </xsl:template>
    
    <xsl:template match="t:fw[@type='pageNum']">
        <span style='background-color:yellow'>
            <xsl:value-of select="."/>
        </span>
    </xsl:template>
    
    <xsl:template match="t:fw[@type='header']">
        <!-- delete -->
    </xsl:template>
    
    <xsl:template match="t:pb">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    
    <xsl:template match="t:milestone">
        <p id="{@n}"> <!-- TODO would it be better to use some other element here? -->
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    
    <!-- TODO adding the lbs as br makes the document really long and confusing, thus omitting for now -->
    
    <!-- 
    <xsl:template match="t:lb">
        <br/>
    </xsl:template>
    -->
    
    <xsl:template match="t:lb">
        <!-- delete -->
    </xsl:template>

    
    <xsl:template match="t:persName">
        <span>
            <xsl:attribute name="class"><xsl:text>person</xsl:text></xsl:attribute>
            <xsl:variable name="normalized-person" select="substring-after(@ref,'#')"/> <!-- mit # -->
            <a style="text-decoration:none;color: inherit;" href="#" data-toggle="tooltip">
                <xsl:attribute name="title">
                    <xsl:for-each select="//t:persName[ancestor::t:teiHeader][@xml:id=$normalized-person]">
                        <xsl:apply-templates/>
                    </xsl:for-each>
                </xsl:attribute>
                <xsl:value-of select="."/>
            </a>
        </span>
    </xsl:template>
    
    
    
</xsl:stylesheet>
