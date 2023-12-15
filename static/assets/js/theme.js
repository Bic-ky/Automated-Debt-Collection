/**
 * Theme: Xeloro - Admin & Dashboard Template
 * Author: Myra Studio
 * File: Main Js
 */


(function ($) {

    'use strict';

    function initMetisMenu() {
        //metis menu
        $("#side-menu").metisMenu();
    }

    function initLeftMenuCollapse() {
        // Left menu collapse
        $('#vertical-menu-btn').on('click', function () {
            $('body').toggleClass('enable-vertical-menu');
        });

        $('.menu-overlay').on('click', function () {
            $('body').removeClass('enable-vertical-menu');
            return;
        });
    }

    function initActiveMenu() {
        // === following js will activate the menu in left side bar based on url ====
        $("#sidebar-menu a").each(function () {
            var pageUrl = window.location.href.split(/[?#]/)[0];
            if (this.href == pageUrl) {
                $(this).addClass("active");
                $(this).parent().addClass("mm-active"); // add active to li of the current link
                $(this).parent().parent().addClass("mm-show");
                $(this).parent().parent().prev().addClass("mm-active"); // add active class to an anchor
                $(this).parent().parent().parent().addClass("mm-active");
                $(this).parent().parent().parent().parent().addClass("mm-show"); // add active to li of the current link
                $(this).parent().parent().parent().parent().parent().addClass("mm-active");
            }
        });
    }

    function initComponents() {
        $(function () {
            $('[data-toggle="tooltip"]').tooltip()
        })

        $(function () {
            $('[data-toggle="popover"]').popover()
        })
    }

    function init() {
        initMetisMenu();
        initLeftMenuCollapse();
        initActiveMenu();
        initComponents();
        Waves.init();
    }

    init();

})(jQuery)




// Add a click event listener to the button
document.getElementById('deleteButton').addEventListener('click', function (event) {
    // Prevent the default action of the anchor tag
    event.preventDefault();

    // Display the confirmation dialog
    Swal.fire({
        title: "Are you sure?",
        text: "You won't be able to revert this!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#d33",
        confirmButtonText: "Yes, delete it!"
    }).then((result) => {
        // Check if the user clicked the confirm button
        if (result.isConfirmed) {
            // Display the success message
            Swal.fire({
                title: "Deleted!",
                text: "Your file has been deleted.",
                icon: "success"
            });

            // Get the href attribute from the anchor tag and navigate to the URL
            window.location.href = document.getElementById('deleteButton').getAttribute('href');
        }
    });
});
