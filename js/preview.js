//
// preview.js  -- Previews markdown and LaTeX using showdown.js and Mathjax
//
// we assume Mathjax.js and showdown.js are present

var MarkdownPreview = function (inputAreaId) {
    var converter = new Showdown.converter();
    return converter.makeHtml(document.getElementById(inputAreaId).value);
};

var Preview = function (sourceId, destId) {
    document.getElementById(destId).innerHTML = MarkdownPreview(sourceId);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, destId]);
};
