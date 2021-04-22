$(document).ready(function () {
    // Initialize  Drag from right on touchscreen
    $('.sidenav').sidenav({ edge: "right", draggable: "True" });
    // Initialize Collapsable Component
    $('.collapsible').collapsible();
    // Initialize Category Dropdown
    $('select').formSelect();
});